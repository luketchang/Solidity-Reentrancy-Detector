contracts = [
# Hacking Distributed Ed. Example - https://hackingdistributed.com/2016/07/13/reentrancy-woes/
"""
contract TokenWithInvariants {
  mapping(address => uint) public balanceOf;
  uint public totalSupply;

  modifier checkInvariants {
    _
    if (this.balance < totalSupply) throw;
  }

  function deposit(uint amount) checkInvariants {
    balanceOf[msg.sender] += amount;
    totalSupply += amount;
  }

  function transfer(address to, uint value) checkInvariants {
    if (balanceOf[msg.sender] >= value) {
      balanceOf[to] += value;
      balanceOf[msg.sender] -= value;
    }
  }

  function withdraw() checkInvariants {
    uint balance = balanceOf[msg.sender];
    if (msg.sender.call.value(balance)()) {
      totalSupply -= balance;
      balanceOf[msg.sender] = 0;
    }
  }
}
""",
# PERSONAL_BANK - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/0x01f8c4e3fa3edeb29e514cba738d87ce8c091d3f.sol
"""
contract PERSONAL_BANK
{
    mapping (address=>uint256) public balances;   
   
    uint public MinSum = 1 ether;
    
    LogFile Log = LogFile(0x0486cF65A2F2F3A392CBEa398AFB7F5f0B72FF46);
    
    bool intitalized;
    
    function SetMinSum(uint _val)
    public
    {
        if(intitalized)revert();
        MinSum = _val;
    }
    
    function SetLogFile(address _log)
    public
    {
        if(intitalized)revert();
        Log = LogFile(_log);
    }
    
    function Initialized()
    public
    {
        intitalized = true;
    }
    
    function Deposit()
    public
    payable
    {
        balances[msg.sender]+= msg.value;
        Log.AddMessage(msg.sender,msg.value,"Put");
    }
    
    function Collect(uint _am)
    public
    payable
    {
        if(balances[msg.sender]>=MinSum && balances[msg.sender]>=_am)
        {
            // <yes> <report> REENTRANCY
            if(msg.sender.call.value(_am)())
            {
                balances[msg.sender]-=_am;
                Log.AddMessage(msg.sender,_am,"Collect");
            }
        }
    }
    
    function() 
    public 
    payable
    {
        Deposit();
    }
    
}
""",
# PrivateBank - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/0x23a91059fdc9579a9fbd0edc5f2ea0bfdb70deb4.sol
"""
contract PrivateBank
{
    mapping (address => uint) public balances;
    
    uint public MinDeposit = 1 ether;
    
    Log TransferLog;
    
    function PrivateBank(address _log)
    {
        TransferLog = Log(_log);
    }
    
    function Deposit()
    public
    payable
    {
        if(msg.value >= MinDeposit)
        {
            balances[msg.sender]+=msg.value;
            TransferLog.AddMessage(msg.sender,msg.value,"Deposit");
        }
    }
    
    function CashOut(uint _am)
    {
        if(_am<=balances[msg.sender])
        {            
            // <yes> <report> REENTRANCY
            if(msg.sender.call.value(_am)())
            {
                balances[msg.sender]-=_am;
                TransferLog.AddMessage(msg.sender,_am,"CashOut");
            }
        }
    }
    
    function() public payable{}    
    
}
""",
# Ownable - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol
"""
contract TokenBank is Token
{
    uint public MinDeposit;
    mapping (address => uint) public Holders;
    
     ///Constructor
    function initTokenBank()
    public
    {
        owner = msg.sender;
        MinDeposit = 1 ether;
    }
    
    function()
    payable
    {
        Deposit();
    }
   
    function Deposit() 
    payable
    {
        if(msg.value>MinDeposit)
        {
            Holders[msg.sender]+=msg.value;
        }
    }
    
    function WitdrawTokenToHolder(address _to,address _token,uint _amount)
    public
    onlyOwner
    {
        if(Holders[_to]>0)
        {
            Holders[_to]=0;
            WithdrawToken(_token,_amount,_to);     
        }
    }
   
    function WithdrawToHolder(address _addr, uint _wei) 
    public
    onlyOwner
    payable
    {
        if(Holders[_addr]>0)
        {
            // <yes> <report> REENTRANCY
            if(_addr.call.value(_wei)())
            {
                Holders[_addr]-=_wei;
            }
        }
    }
}
""",
# X_WALLET - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/0x93c32845fae42c83a70e5f06214c8433665c2ab5.sol
"""
contract X_WALLET
{
    function Put(uint _unlockTime)
    public
    payable
    {
        var acc = Acc[msg.sender];
        acc.balance += msg.value;
        acc.unlockTime = _unlockTime>now?_unlockTime:now;
        LogFile.AddMessage(msg.sender,msg.value,"Put");
    }

    function Collect(uint _am)
    public
    payable
    {
        var acc = Acc[msg.sender];
        if( acc.balance>=MinSum && acc.balance>=_am && now>acc.unlockTime)
        {
            // <yes> <report> REENTRANCY
            if(msg.sender.call.value(_am)())
            {
                acc.balance-=_am;
                LogFile.AddMessage(msg.sender,_am,"Collect");
            }
        }
    }

    function() 
    public 
    payable
    {
        Put(0);
    }

    struct Holder   
    {
        uint unlockTime;
        uint balance;
    }

    mapping (address => Holder) public Acc;

    Log LogFile;

    uint public MinSum = 1 ether;    

    function X_WALLET(address log) public{
        LogFile = Log(log);
    }
}
""",
# ETHFUND - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/0x941d225236464a25eb18076df7da6a91d0f95e9e.sol
"""
contract ETH_FUND
{
    mapping (address => uint) public balances;
    
    uint public MinDeposit = 1 ether;
    
    Log TransferLog;
    
    uint lastBlock;
    
    function ETH_FUND(address _log)
    public 
    {
        TransferLog = Log(_log);
    }
    
    function Deposit()
    public
    payable
    {
        if(msg.value > MinDeposit)
        {
            balances[msg.sender]+=msg.value;
            TransferLog.AddMessage(msg.sender,msg.value,"Deposit");
            lastBlock = block.number;
        }
    }
    
    function CashOut(uint _am)
    public
    payable
    {
        if(_am<=balances[msg.sender]&&block.number>lastBlock)
        {
            // <yes> <report> REENTRANCY
            if(msg.sender.call.value(_am)())
            {
                balances[msg.sender]-=_am;
                TransferLog.AddMessage(msg.sender,_am,"CashOut");
            }
        }
    }
    
    function() public payable{}    
    
}
""",
# EtherBank - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/etherbank.sol
"""
contract EtherBank{
    mapping (address => uint) userBalances;
    function getBalance(address user) constant returns(uint) {  
		return userBalances[user];
	}

	function addToBalance() {  
		userBalances[msg.sender] += msg.value;
	}

	function withdrawBalance() {  
		uint amountToWithdraw = userBalances[msg.sender];
        // <yes> <report> REENTRANCY
		if (!(msg.sender.call.value(amountToWithdraw)())) { throw; }
		userBalances[msg.sender] = 0;
	}    
}
""",
# EtherStore - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/etherstore.sol
"""
contract EtherStore {

    uint256 public withdrawalLimit = 1 ether;
    mapping(address => uint256) public lastWithdrawTime;
    mapping(address => uint256) public balances;

    function depositFunds() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdrawFunds (uint256 _weiToWithdraw) public {
        require(balances[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
        require(_weiToWithdraw <= withdrawalLimit);
        // limit the time allowed to withdraw
        require(now >= lastWithdrawTime[msg.sender] + 1 weeks);
        // <yes> <report> REENTRANCY
        require(msg.sender.call.value(_weiToWithdraw)());
        balances[msg.sender] -= _weiToWithdraw;
        lastWithdrawTime[msg.sender] = now;
    }
}
""",
# Reetrance - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/reentrance.sol
"""
contract Reentrance {

  mapping(address => uint) public balances;

  function donate(address _to) public payable {
    balances[_to] += msg.value;
  }

  function balanceOf(address _who) public view returns (uint balance) {
    return balances[_who];
  }

  function withdraw(uint _amount) public {
    if(balances[msg.sender] >= _amount) {
      // <yes> <report> REENTRANCY
      if(msg.sender.call.value(_amount)()) {
        _amount;
      }
      balances[msg.sender] -= _amount;
    }
  }

  function() public payable {}
}
""",
# reentrancy_bonus - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/reentrancy_bonus.sol
"""
contract Reentrancy_bonus{

    // INSECURE
    mapping (address => uint) private userBalances;
    mapping (address => bool) private claimedBonus;
    mapping (address => uint) private rewardsForA;

    function withdrawReward(address recipient) public {
        uint amountToWithdraw = rewardsForA[recipient];
        rewardsForA[recipient] = 0;
        (bool success, ) = recipient.call.value(amountToWithdraw)("");
        require(success);
    }

    function getFirstWithdrawalBonus(address recipient) public {
        require(!claimedBonus[recipient]); // Each recipient should only be able to claim the bonus once

        rewardsForA[recipient] += 100;
        // <yes> <report> REENTRANCY
        withdrawReward(recipient); // At this point, the caller will be able to execute getFirstWithdrawalBonus again.
        claimedBonus[recipient] = true;
    }
}
""",
# Reentrancy_cross_function - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/reentrancy_cross_function.sol
"""
contract Reentrancy_cross_function {

    // INSECURE
    mapping (address => uint) private userBalances;

    function transfer(address to, uint amount) {
        if (userBalances[msg.sender] >= amount) {
            userBalances[to] += amount;
            userBalances[msg.sender] -= amount;
        }
    }

    function withdrawBalance() public {
        uint amountToWithdraw = userBalances[msg.sender];
        // <yes> <report> REENTRANCY
        (bool success, ) = msg.sender.call.value(amountToWithdraw)(""); // At this point, the caller's code is executed, and can call transfer()
        require(success);
        userBalances[msg.sender] = 0;
    }
}
""",
# ReentrancyDAO - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/reentrancy_dao.sol
"""
contract ReentrancyDAO {
    mapping (address => uint) credit;
    uint balance;

    function withdrawAll() public {
        uint oCredit = credit[msg.sender];
        if (oCredit > 0) {
            balance -= oCredit;
            // <yes> <report> REENTRANCY
            bool callResult = msg.sender.call.value(oCredit)();
            require (callResult);
            credit[msg.sender] = 0;
        }
    }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        balance += msg.value;
    }
}
""",
# Reentrancy_insecure - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/reentrancy_insecure.sol
"""
contract Reentrancy_insecure {

    // INSECURE
    mapping (address => uint) private userBalances;

    function withdrawBalance() public {
        uint amountToWithdraw = userBalances[msg.sender];
        // <yes> <report> REENTRANCY
        (bool success, ) = msg.sender.call.value(amountToWithdraw)(""); // At this point, the caller's code is executed, and can call withdrawBalance again
        require(success);
        userBalances[msg.sender] = 0;
    }
}
""",
# reentrancy_simple - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/reentrancy_simple.sol
"""
contract Reentrance {
     mapping (address => uint) userBalance;

     function getBalance(address u) constant returns(uint){
         return userBalance[u];
     }

     function addToBalance() payable{
         userBalance[msg.sender] += msg.value;
     }

     function withdrawBalance(){
         // send userBalance[msg.sender] ethers to msg.sender
         // if mgs.sender is a contract, it will call its fallback function
         // <yes> <report> REENTRANCY
         if( ! (msg.sender.call.value(userBalance[msg.sender])() ) ){
             throw;
         }
         userBalance[msg.sender] = 0;
     }
 }
""",
# SimpleDAO - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/simple_dao.sol
"""
contract SimpleDAO {
  mapping (address => uint) public credit;

  function donate(address to) payable {
    credit[to] += msg.value;
  }

  function withdraw(uint amount) {
    if (credit[msg.sender]>= amount) {
      // <yes> <report> REENTRANCY
      bool res = msg.sender.call.value(amount)();
      credit[msg.sender]-=amount;
    }
  }

  function queryCredit(address to) returns (uint){
    return credit[to];
  }
}
""",
# LedgerChannel (spankchain) - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/spank_chain_payment.sol
"""
contract LedgerChannel {
    string public constant NAME = "Ledger Channel";
    string public constant VERSION = "0.0.1";

    uint256 public numChannels = 0;

    event DidLCOpen (
        bytes32 indexed channelId,
        address indexed partyA,
        address indexed partyI,
        uint256 ethBalanceA,
        address token,
        uint256 tokenBalanceA,
        uint256 LCopenTimeout
    );

    event DidLCJoin (
        bytes32 indexed channelId,
        uint256 ethBalanceI,
        uint256 tokenBalanceI
    );

    event DidLCDeposit (
        bytes32 indexed channelId,
        address indexed recipient,
        uint256 deposit,
        bool isToken
    );

    event DidLCUpdateState (
        bytes32 indexed channelId,
        uint256 sequence,
        uint256 numOpenVc,
        uint256 ethBalanceA,
        uint256 tokenBalanceA,
        uint256 ethBalanceI,
        uint256 tokenBalanceI,
        bytes32 vcRoot,
        uint256 updateLCtimeout
    );

    event DidLCClose (
        bytes32 indexed channelId,
        uint256 sequence,
        uint256 ethBalanceA,
        uint256 tokenBalanceA,
        uint256 ethBalanceI,
        uint256 tokenBalanceI
    );

    event DidVCInit (
        bytes32 indexed lcId,
        bytes32 indexed vcId,
        bytes proof,
        uint256 sequence,
        address partyA,
        address partyB,
        uint256 balanceA,
        uint256 balanceB
    );

    event DidVCSettle (
        bytes32 indexed lcId,
        bytes32 indexed vcId,
        uint256 updateSeq,
        uint256 updateBalA,
        uint256 updateBalB,
        address challenger,
        uint256 updateVCtimeout
    );

    event DidVCClose(
        bytes32 indexed lcId,
        bytes32 indexed vcId,
        uint256 balanceA,
        uint256 balanceB
    );

    struct Channel {
        //TODO: figure out if it's better just to split arrays by balances/deposits instead of eth/erc20
        address[2] partyAddresses; // 0: partyA 1: partyI
        uint256[4] ethBalances; // 0: balanceA 1:balanceI 2:depositedA 3:depositedI
        uint256[4] erc20Balances; // 0: balanceA 1:balanceI 2:depositedA 3:depositedI
        uint256[2] initialDeposit; // 0: eth 1: tokens
        uint256 sequence;
        uint256 confirmTime;
        bytes32 VCrootHash;
        uint256 LCopenTimeout;
        uint256 updateLCtimeout; // when update LC times out
        bool isOpen; // true when both parties have joined
        bool isUpdateLCSettling;
        uint256 numOpenVC;
        HumanStandardToken token;
    }

    // virtual-channel state
    struct VirtualChannel {
        bool isClose;
        bool isInSettlementState;
        uint256 sequence;
        address challenger; // Initiator of challenge
        uint256 updateVCtimeout; // when update VC times out
        // channel state
        address partyA; // VC participant A
        address partyB; // VC participant B
        address partyI; // LC hub
        uint256[2] ethBalances;
        uint256[2] erc20Balances;
        uint256[2] bond;
        HumanStandardToken token;
    }

    mapping(bytes32 => VirtualChannel) public virtualChannels;
    mapping(bytes32 => Channel) public Channels;

    function createChannel(
        bytes32 _lcID,
        address _partyI,
        uint256 _confirmTime,
        address _token,
        uint256[2] _balances // [eth, token]
    )
        public
        payable
    {
        require(Channels[_lcID].partyAddresses[0] == address(0), "Channel has already been created.");
        require(_partyI != 0x0, "No partyI address provided to LC creation");
        require(_balances[0] >= 0 && _balances[1] >= 0, "Balances cannot be negative");
        // Set initial ledger channel state
        // Alice must execute this and we assume the initial state
        // to be signed from this requirement
        // Alternative is to check a sig as in joinChannel
        Channels[_lcID].partyAddresses[0] = msg.sender;
        Channels[_lcID].partyAddresses[1] = _partyI;

        if(_balances[0] != 0) {
            require(msg.value == _balances[0], "Eth balance does not match sent value");
            Channels[_lcID].ethBalances[0] = msg.value;
        }
        if(_balances[1] != 0) {
            Channels[_lcID].token = HumanStandardToken(_token);
            require(Channels[_lcID].token.transferFrom(msg.sender, this, _balances[1]),"CreateChannel: token transfer failure");
            Channels[_lcID].erc20Balances[0] = _balances[1];
        }

        Channels[_lcID].sequence = 0;
        Channels[_lcID].confirmTime = _confirmTime;
        // is close flag, lc state sequence, number open vc, vc root hash, partyA...
        //Channels[_lcID].stateHash = keccak256(uint256(0), uint256(0), uint256(0), bytes32(0x0), bytes32(msg.sender), bytes32(_partyI), balanceA, balanceI);
        Channels[_lcID].LCopenTimeout = now + _confirmTime;
        Channels[_lcID].initialDeposit = _balances;

        emit DidLCOpen(_lcID, msg.sender, _partyI, _balances[0], _token, _balances[1], Channels[_lcID].LCopenTimeout);
    }

    function LCOpenTimeout(bytes32 _lcID) public {
        require(msg.sender == Channels[_lcID].partyAddresses[0] && Channels[_lcID].isOpen == false);
        require(now > Channels[_lcID].LCopenTimeout);

        if(Channels[_lcID].initialDeposit[0] != 0) {
            // <yes> <report> REENTRANCY
            Channels[_lcID].partyAddresses[0].transfer(Channels[_lcID].ethBalances[0]);
        }
        if(Channels[_lcID].initialDeposit[1] != 0) {
            // <yes> <report> REENTRANCY
            require(Channels[_lcID].token.transfer(Channels[_lcID].partyAddresses[0], Channels[_lcID].erc20Balances[0]),"CreateChannel: token transfer failure");
        }

        emit DidLCClose(_lcID, 0, Channels[_lcID].ethBalances[0], Channels[_lcID].erc20Balances[0], 0, 0);

        // only safe to delete since no action was taken on this channel
        delete Channels[_lcID];
    }

    function joinChannel(bytes32 _lcID, uint256[2] _balances) public payable {
        // require the channel is not open yet
        require(Channels[_lcID].isOpen == false);
        require(msg.sender == Channels[_lcID].partyAddresses[1]);

        if(_balances[0] != 0) {
            require(msg.value == _balances[0], "state balance does not match sent value");
            Channels[_lcID].ethBalances[1] = msg.value;
        }
        if(_balances[1] != 0) {
            require(Channels[_lcID].token.transferFrom(msg.sender, this, _balances[1]),"joinChannel: token transfer failure");
            Channels[_lcID].erc20Balances[1] = _balances[1];
        }

        Channels[_lcID].initialDeposit[0]+=_balances[0];
        Channels[_lcID].initialDeposit[1]+=_balances[1];
        // no longer allow joining functions to be called
        Channels[_lcID].isOpen = true;
        numChannels++;

        emit DidLCJoin(_lcID, _balances[0], _balances[1]);
    }


    // additive updates of monetary state
    // TODO check this for attack vectors
    function deposit(bytes32 _lcID, address recipient, uint256 _balance, bool isToken) public payable {
        require(Channels[_lcID].isOpen == true, "Tried adding funds to a closed channel");
        require(recipient == Channels[_lcID].partyAddresses[0] || recipient == Channels[_lcID].partyAddresses[1]);

        //if(Channels[_lcID].token)

        if (Channels[_lcID].partyAddresses[0] == recipient) {
            if(isToken) {
                require(Channels[_lcID].token.transferFrom(msg.sender, this, _balance),"deposit: token transfer failure");
                Channels[_lcID].erc20Balances[2] += _balance;
            } else {
                require(msg.value == _balance, "state balance does not match sent value");
                Channels[_lcID].ethBalances[2] += msg.value;
            }
        }

        if (Channels[_lcID].partyAddresses[1] == recipient) {
            if(isToken) {
                require(Channels[_lcID].token.transferFrom(msg.sender, this, _balance),"deposit: token transfer failure");
                Channels[_lcID].erc20Balances[3] += _balance;
            } else {
                require(msg.value == _balance, "state balance does not match sent value");
                Channels[_lcID].ethBalances[3] += msg.value;
            }
        }

        emit DidLCDeposit(_lcID, recipient, _balance, isToken);
    }

    // TODO: Check there are no open virtual channels, the client should have cought this before signing a close LC state update
    function consensusCloseChannel(
        bytes32 _lcID,
        uint256 _sequence,
        uint256[4] _balances, // 0: ethBalanceA 1:ethBalanceI 2:tokenBalanceA 3:tokenBalanceI
        string _sigA,
        string _sigI
    )
        public
    {
        // assume num open vc is 0 and root hash is 0x0
        //require(Channels[_lcID].sequence < _sequence);
        require(Channels[_lcID].isOpen == true);
        uint256 totalEthDeposit = Channels[_lcID].initialDeposit[0] + Channels[_lcID].ethBalances[2] + Channels[_lcID].ethBalances[3];
        uint256 totalTokenDeposit = Channels[_lcID].initialDeposit[1] + Channels[_lcID].erc20Balances[2] + Channels[_lcID].erc20Balances[3];
        require(totalEthDeposit == _balances[0] + _balances[1]);
        require(totalTokenDeposit == _balances[2] + _balances[3]);

        bytes32 _state = keccak256(
            abi.encodePacked(
                _lcID,
                true,
                _sequence,
                uint256(0),
                bytes32(0x0),
                Channels[_lcID].partyAddresses[0],
                Channels[_lcID].partyAddresses[1],
                _balances[0],
                _balances[1],
                _balances[2],
                _balances[3]
            )
        );

        require(Channels[_lcID].partyAddresses[0] == ECTools.recoverSigner(_state, _sigA));
        require(Channels[_lcID].partyAddresses[1] == ECTools.recoverSigner(_state, _sigI));

        Channels[_lcID].isOpen = false;

        if(_balances[0] != 0 || _balances[1] != 0) {
            Channels[_lcID].partyAddresses[0].transfer(_balances[0]);
            Channels[_lcID].partyAddresses[1].transfer(_balances[1]);
        }

        if(_balances[2] != 0 || _balances[3] != 0) {
            require(Channels[_lcID].token.transfer(Channels[_lcID].partyAddresses[0], _balances[2]),"happyCloseChannel: token transfer failure");
            require(Channels[_lcID].token.transfer(Channels[_lcID].partyAddresses[1], _balances[3]),"happyCloseChannel: token transfer failure");
        }

        numChannels--;

        emit DidLCClose(_lcID, _sequence, _balances[0], _balances[1], _balances[2], _balances[3]);
    }

    // Byzantine functions

    function updateLCstate(
        bytes32 _lcID,
        uint256[6] updateParams, // [sequence, numOpenVc, ethbalanceA, ethbalanceI, tokenbalanceA, tokenbalanceI]
        bytes32 _VCroot,
        string _sigA,
        string _sigI
    )
        public
    {
        Channel storage channel = Channels[_lcID];
        require(channel.isOpen);
        require(channel.sequence < updateParams[0]); // do same as vc sequence check
        require(channel.ethBalances[0] + channel.ethBalances[1] >= updateParams[2] + updateParams[3]);
        require(channel.erc20Balances[0] + channel.erc20Balances[1] >= updateParams[4] + updateParams[5]);

        if(channel.isUpdateLCSettling == true) {
            require(channel.updateLCtimeout > now);
        }

        bytes32 _state = keccak256(
            abi.encodePacked(
                _lcID,
                false,
                updateParams[0],
                updateParams[1],
                _VCroot,
                channel.partyAddresses[0],
                channel.partyAddresses[1],
                updateParams[2],
                updateParams[3],
                updateParams[4],
                updateParams[5]
            )
        );

        require(channel.partyAddresses[0] == ECTools.recoverSigner(_state, _sigA));
        require(channel.partyAddresses[1] == ECTools.recoverSigner(_state, _sigI));

        // update LC state
        channel.sequence = updateParams[0];
        channel.numOpenVC = updateParams[1];
        channel.ethBalances[0] = updateParams[2];
        channel.ethBalances[1] = updateParams[3];
        channel.erc20Balances[0] = updateParams[4];
        channel.erc20Balances[1] = updateParams[5];
        channel.VCrootHash = _VCroot;
        channel.isUpdateLCSettling = true;
        channel.updateLCtimeout = now + channel.confirmTime;

        // make settlement flag

        emit DidLCUpdateState (
            _lcID,
            updateParams[0],
            updateParams[1],
            updateParams[2],
            updateParams[3],
            updateParams[4],
            updateParams[5],
            _VCroot,
            channel.updateLCtimeout
        );
    }

    // supply initial state of VC to "prime" the force push game
    function initVCstate(
        bytes32 _lcID,
        bytes32 _vcID,
        bytes _proof,
        address _partyA,
        address _partyB,
        uint256[2] _bond,
        uint256[4] _balances, // 0: ethBalanceA 1:ethBalanceI 2:tokenBalanceA 3:tokenBalanceI
        string sigA
    )
        public
    {
        require(Channels[_lcID].isOpen, "LC is closed.");
        // sub-channel must be open
        require(!virtualChannels[_vcID].isClose, "VC is closed.");
        // Check time has passed on updateLCtimeout and has not passed the time to store a vc state
        require(Channels[_lcID].updateLCtimeout < now, "LC timeout not over.");
        // prevent rentry of initializing vc state
        require(virtualChannels[_vcID].updateVCtimeout == 0);
        // partyB is now Ingrid
        bytes32 _initState = keccak256(
            abi.encodePacked(_vcID, uint256(0), _partyA, _partyB, _bond[0], _bond[1], _balances[0], _balances[1], _balances[2], _balances[3])
        );

        // Make sure Alice has signed initial vc state (A/B in oldState)
        require(_partyA == ECTools.recoverSigner(_initState, sigA));

        // Check the oldState is in the root hash
        require(_isContained(_initState, _proof, Channels[_lcID].VCrootHash) == true);

        virtualChannels[_vcID].partyA = _partyA; // VC participant A
        virtualChannels[_vcID].partyB = _partyB; // VC participant B
        virtualChannels[_vcID].sequence = uint256(0);
        virtualChannels[_vcID].ethBalances[0] = _balances[0];
        virtualChannels[_vcID].ethBalances[1] = _balances[1];
        virtualChannels[_vcID].erc20Balances[0] = _balances[2];
        virtualChannels[_vcID].erc20Balances[1] = _balances[3];
        virtualChannels[_vcID].bond = _bond;
        virtualChannels[_vcID].updateVCtimeout = now + Channels[_lcID].confirmTime;
        virtualChannels[_vcID].isInSettlementState = true;

        emit DidVCInit(_lcID, _vcID, _proof, uint256(0), _partyA, _partyB, _balances[0], _balances[1]);
    }

    //TODO: verify state transition since the hub did not agree to this state
    // make sure the A/B balances are not beyond ingrids bonds
    // Params: vc init state, vc final balance, vcID
    function settleVC(
        bytes32 _lcID,
        bytes32 _vcID,
        uint256 updateSeq,
        address _partyA,
        address _partyB,
        uint256[4] updateBal, // [ethupdateBalA, ethupdateBalB, tokenupdateBalA, tokenupdateBalB]
        string sigA
    )
        public
    {
        require(Channels[_lcID].isOpen, "LC is closed.");
        // sub-channel must be open
        require(!virtualChannels[_vcID].isClose, "VC is closed.");
        require(virtualChannels[_vcID].sequence < updateSeq, "VC sequence is higher than update sequence.");
        require(
            virtualChannels[_vcID].ethBalances[1] < updateBal[1] && virtualChannels[_vcID].erc20Balances[1] < updateBal[3],
            "State updates may only increase recipient balance."
        );
        require(
            virtualChannels[_vcID].bond[0] == updateBal[0] + updateBal[1] &&
            virtualChannels[_vcID].bond[1] == updateBal[2] + updateBal[3],
            "Incorrect balances for bonded amount");
        // Check time has passed on updateLCtimeout and has not passed the time to store a vc state
        // virtualChannels[_vcID].updateVCtimeout should be 0 on uninitialized vc state, and this should
        // fail if initVC() isn't called first
        // require(Channels[_lcID].updateLCtimeout < now && now < virtualChannels[_vcID].updateVCtimeout);
        require(Channels[_lcID].updateLCtimeout < now); // for testing!

        bytes32 _updateState = keccak256(
            abi.encodePacked(
                _vcID,
                updateSeq,
                _partyA,
                _partyB,
                virtualChannels[_vcID].bond[0],
                virtualChannels[_vcID].bond[1],
                updateBal[0],
                updateBal[1],
                updateBal[2],
                updateBal[3]
            )
        );

        // Make sure Alice has signed a higher sequence new state
        require(virtualChannels[_vcID].partyA == ECTools.recoverSigner(_updateState, sigA));

        // store VC data
        // we may want to record who is initiating on-chain settles
        virtualChannels[_vcID].challenger = msg.sender;
        virtualChannels[_vcID].sequence = updateSeq;

        // channel state
        virtualChannels[_vcID].ethBalances[0] = updateBal[0];
        virtualChannels[_vcID].ethBalances[1] = updateBal[1];
        virtualChannels[_vcID].erc20Balances[0] = updateBal[2];
        virtualChannels[_vcID].erc20Balances[1] = updateBal[3];

        virtualChannels[_vcID].updateVCtimeout = now + Channels[_lcID].confirmTime;

        emit DidVCSettle(_lcID, _vcID, updateSeq, updateBal[0], updateBal[1], msg.sender, virtualChannels[_vcID].updateVCtimeout);
    }

    function closeVirtualChannel(bytes32 _lcID, bytes32 _vcID) public {
        // require(updateLCtimeout > now)
        require(Channels[_lcID].isOpen, "LC is closed.");
        require(virtualChannels[_vcID].isInSettlementState, "VC is not in settlement state.");
        require(virtualChannels[_vcID].updateVCtimeout < now, "Update vc timeout has not elapsed.");
        require(!virtualChannels[_vcID].isClose, "VC is already closed");
        // reduce the number of open virtual channels stored on LC
        Channels[_lcID].numOpenVC--;
        // close vc flags
        virtualChannels[_vcID].isClose = true;
        // re-introduce the balances back into the LC state from the settled VC
        // decide if this lc is alice or bob in the vc
        if(virtualChannels[_vcID].partyA == Channels[_lcID].partyAddresses[0]) {
            Channels[_lcID].ethBalances[0] += virtualChannels[_vcID].ethBalances[0];
            Channels[_lcID].ethBalances[1] += virtualChannels[_vcID].ethBalances[1];

            Channels[_lcID].erc20Balances[0] += virtualChannels[_vcID].erc20Balances[0];
            Channels[_lcID].erc20Balances[1] += virtualChannels[_vcID].erc20Balances[1];
        } else if (virtualChannels[_vcID].partyB == Channels[_lcID].partyAddresses[0]) {
            Channels[_lcID].ethBalances[0] += virtualChannels[_vcID].ethBalances[1];
            Channels[_lcID].ethBalances[1] += virtualChannels[_vcID].ethBalances[0];

            Channels[_lcID].erc20Balances[0] += virtualChannels[_vcID].erc20Balances[1];
            Channels[_lcID].erc20Balances[1] += virtualChannels[_vcID].erc20Balances[0];
        }

        emit DidVCClose(_lcID, _vcID, virtualChannels[_vcID].erc20Balances[0], virtualChannels[_vcID].erc20Balances[1]);
    }


    // todo: allow ethier lc.end-user to nullify the settled LC state and return to off-chain
    function byzantineCloseChannel(bytes32 _lcID) public {
        Channel storage channel = Channels[_lcID];

        // check settlement flag
        require(channel.isOpen, "Channel is not open");
        require(channel.isUpdateLCSettling == true);
        require(channel.numOpenVC == 0);
        require(channel.updateLCtimeout < now, "LC timeout over.");

        // if off chain state update didnt reblance deposits, just return to deposit owner
        uint256 totalEthDeposit = channel.initialDeposit[0] + channel.ethBalances[2] + channel.ethBalances[3];
        uint256 totalTokenDeposit = channel.initialDeposit[1] + channel.erc20Balances[2] + channel.erc20Balances[3];

        uint256 possibleTotalEthBeforeDeposit = channel.ethBalances[0] + channel.ethBalances[1];
        uint256 possibleTotalTokenBeforeDeposit = channel.erc20Balances[0] + channel.erc20Balances[1];

        if(possibleTotalEthBeforeDeposit < totalEthDeposit) {
            channel.ethBalances[0]+=channel.ethBalances[2];
            channel.ethBalances[1]+=channel.ethBalances[3];
        } else {
            require(possibleTotalEthBeforeDeposit == totalEthDeposit);
        }

        if(possibleTotalTokenBeforeDeposit < totalTokenDeposit) {
            channel.erc20Balances[0]+=channel.erc20Balances[2];
            channel.erc20Balances[1]+=channel.erc20Balances[3];
        } else {
            require(possibleTotalTokenBeforeDeposit == totalTokenDeposit);
        }

        // reentrancy
        uint256 ethbalanceA = channel.ethBalances[0];
        uint256 ethbalanceI = channel.ethBalances[1];
        uint256 tokenbalanceA = channel.erc20Balances[0];
        uint256 tokenbalanceI = channel.erc20Balances[1];

        channel.ethBalances[0] = 0;
        channel.ethBalances[1] = 0;
        channel.erc20Balances[0] = 0;
        channel.erc20Balances[1] = 0;

        if(ethbalanceA != 0 || ethbalanceI != 0) {
            channel.partyAddresses[0].transfer(ethbalanceA);
            channel.partyAddresses[1].transfer(ethbalanceI);
        }

        if(tokenbalanceA != 0 || tokenbalanceI != 0) {
            require(
                channel.token.transfer(channel.partyAddresses[0], tokenbalanceA),
                "byzantineCloseChannel: token transfer failure"
            );
            require(
                channel.token.transfer(channel.partyAddresses[1], tokenbalanceI),
                "byzantineCloseChannel: token transfer failure"
            );
        }

        channel.isOpen = false;
        numChannels--;

        emit DidLCClose(_lcID, channel.sequence, ethbalanceA, ethbalanceI, tokenbalanceA, tokenbalanceI);
    }

    function _isContained(bytes32 _hash, bytes _proof, bytes32 _root) internal pure returns (bool) {
        bytes32 cursor = _hash;
        bytes32 proofElem;

        for (uint256 i = 64; i <= _proof.length; i += 32) {
            assembly { proofElem := mload(add(_proof, i)) }

            if (cursor < proofElem) {
                cursor = keccak256(abi.encodePacked(cursor, proofElem));
            } else {
                cursor = keccak256(abi.encodePacked(proofElem, cursor));
            }
        }

        return cursor == _root;
    }

    //Struct Getters
    function getChannel(bytes32 id) public view returns (
        address[2],
        uint256[4],
        uint256[4],
        uint256[2],
        uint256,
        uint256,
        bytes32,
        uint256,
        uint256,
        bool,
        bool,
        uint256
    ) {
        Channel memory channel = Channels[id];
        return (
            channel.partyAddresses,
            channel.ethBalances,
            channel.erc20Balances,
            channel.initialDeposit,
            channel.sequence,
            channel.confirmTime,
            channel.VCrootHash,
            channel.LCopenTimeout,
            channel.updateLCtimeout,
            channel.isOpen,
            channel.isUpdateLCSettling,
            channel.numOpenVC
        );
    }

    function getVirtualChannel(bytes32 id) public view returns(
        bool,
        bool,
        uint256,
        address,
        uint256,
        address,
        address,
        address,
        uint256[2],
        uint256[2],
        uint256[2]
    ) {
        VirtualChannel memory virtualChannel = virtualChannels[id];
        return(
            virtualChannel.isClose,
            virtualChannel.isInSettlementState,
            virtualChannel.sequence,
            virtualChannel.challenger,
            virtualChannel.updateVCtimeout,
            virtualChannel.partyA,
            virtualChannel.partyB,
            virtualChannel.partyI,
            virtualChannel.ethBalances,
            virtualChannel.erc20Balances,
            virtualChannel.bond
        );
    }
}
""",
# Victim - https://github.com/ltchang2019/GraphDeeSmartContract/blob/master/contract_data/reentrancy/source_code/Victim.sol
"""
contract Victim {
   
  mapping(address => uint) public balances;
   
  function withdraw(uint _amount) public {
    if(balances[msg.sender] >= _amount) {
        if(msg.sender.call.value(_amount)()) {
            _amount;
        }
        balances[msg.sender] -= _amount;
    }
  }
  function deposit() payable {}
}
""",
# DumbDAO - https://github.com/ltchang2019/GraphDeeSmartContract/blob/master/contract_data/reentrancy/source_code/dumbDAO.sol
"""
contract dumbDAO {

  event PaymentCalled(address payee, uint amount);
  event TokensBought(address buyer, uint amount);
  event TokensTransfered(address from, address to, uint amount);
  event InsufficientFunds(uint bal, uint amount);


  mapping (address => uint) public balances;

  function buyTokens(){
    balances[msg.sender] += msg.value;
    TokensBought(msg.sender, msg.value);
  }

  function transferTokens(address _to, uint _amount){
    if (balances[msg.sender] < _amount)
      throw;
    balances[_to]=_amount;
    balances[msg.sender]-=_amount;
    TokensTransfered(msg.sender, _to, _amount);
  }

  function withdraw(address _recipient) returns (bool) {
    if (balances[msg.sender] == 0){
        InsufficientFunds(balances[msg.sender],balances[msg.sender]);
        throw;
    }
    PaymentCalled(_recipient, balances[msg.sender]);
    if (_recipient.call.value(balances[msg.sender])()) {  
        balances[msg.sender] = 0;
        return true;
    }
  }

}
""",
# SendBalance - https://github.com/ltchang2019/GraphDeeSmartContract/blob/master/contract_data/reentrancy/source_code/SendBalance.sol
"""
contract SendBalance {
 mapping (address => uint) userBalances ;
 bool withdrawn = false ;
 function getBalance(address u) constant returns (uint){
    return userBalances[u];
 }
 function addToBalance() {
    userBalances msg.sender] += msg.value ;
 }
 function withdrawBalance(){
    if (!(msg.sender.call.value(userBalances[msg.sender])())) { throw ; }
    userBalances[msg.sender] = 0;
 }
}
""",
# Reetrance_01 - https://github.com/ltchang2019/GraphDeeSmartContract/blob/master/contract_data/reentrancy/source_code/Reentrance_01.sol
"""
contract Reentrance {
    mapping (address => uint) userBalance;
   
    function getBalance(address u) constant returns(uint){
        return userBalance[u];
    }

    function addToBalance() payable{
        userBalance[msg.sender] += msg.value;
    }   

    function withdrawBalance(){
         
         
        if(!(msg.sender.call.value(userBalance[msg.sender])())){
            throw;
        }
        userBalance[msg.sender] = 0;
    }
   
}
""",
# Reentrance_02 - https://github.com/ltchang2019/GraphDeeSmartContract/blob/master/contract_data/reentrancy/source_code/Reentrance_02.sol
"""
contract Reentrance {

  mapping(address => uint) public balances;

  function donate(address _to) public payable {
    balances[_to] += msg.value;
  }

  function balanceOf(address _who) public view returns (uint balance) {
    return balances[_who];
  }

  function withdraw(uint _amount) public {
    if(balances[msg.sender] >= _amount) {
      if(msg.sender.call.value(_amount)()) {
        _amount;
      }
      balances[msg.sender] -= _amount;
    }
  }

  function() public payable {}
}
""",
# SimpleDAOFixed - https://github.com/ltchang2019/GraphDeeSmartContract/blob/master/contract_data/reentrancy/source_code/simple_dao_fixed.sol
"""
contract SimpleDAO {
  mapping (address => uint) public credit;
    
  function donate(address to) payable public{
    credit[to] += msg.value;
  }
    
  function withdraw(uint amount) public {
    if (credit[msg.sender]>= amount) {
      credit[msg.sender]-=amount;
      require(msg.sender.call.value(amount)());
    }
  }  

  function queryCredit(address to) view public returns (uint){
    return credit[to];
  }
}
""",
# ERC223 - https://github.com/ltchang2019/GNNSCVulDetector/blob/master/data/reentrancy/solidity_contract/10107.sol
"""
contract MyToken is ERC223 {
    using SafeMath for uint;

    mapping(address => uint) balances;  

    string public name;
    string public symbol;
    uint8 public decimals;
    uint public totalSupply;

 
    constructor(string _name, string _symbol, uint8 _decimals, uint _totalSupply) public {
		name = _name;
		symbol = _symbol;
		decimals = _decimals;
		totalSupply = _totalSupply;
		balances[msg.sender] = _totalSupply;
	}

    function name() public view returns (string) {
		 return name;
    }

    function symbol() public view returns (string) {
		return symbol;
	}

    function decimals() public view returns (uint8) {
    	return decimals;
    }

    function totalSupply() public view returns (uint) {
    	return totalSupply;
    }


	function balanceOf(address owner) public view returns (uint) {
		return balances[owner];
	}

	function transfer(address to, uint value, bytes data) public returns (bool) {
		if(balanceOf(msg.sender) < value) revert();
		balances[msg.sender] = balances[msg.sender].sub(value);
		balances[to] = balances[to].add(value);
		if(isContract(to)) {
			ERC223ReceivingContract receiver = ERC223ReceivingContract(to);
			receiver.tokenFallback(msg.sender, value, data);
		}
		emit Transfer(msg.sender, to, value, data);
		return true;
	}

	function transfer(address to, uint value) public returns (bool) {
		if(balanceOf(msg.sender) < value) revert();
		bytes memory empty;

		balances[msg.sender] = balances[msg.sender].sub(value);
        balances[to] = balances[to].add(value);
        if(isContract(to)) {
            ERC223ReceivingContract receiver = ERC223ReceivingContract(to);
            receiver.tokenFallback(msg.sender, value, empty);
        }
        emit Transfer(msg.sender, to, value, empty);
        return true;
	}

	function transfer(address to, uint value, bytes data, string customFallback) public returns (bool) {
		if(balanceOf(msg.sender) < value) revert();
		balances[msg.sender] = balances[msg.sender].sub(value);
        balances[to] = balances[to].add(value);
		if (isContract(to)) {
            assert(to.call.value(0)(bytes4(keccak256(customFallback)), msg.sender, value, data));
        }
        emit Transfer(msg.sender, to, value, data);
        return true;
	}

	function isContract(address addr) private view returns (bool) {
		uint len;
		assembly {
			len := extcodesize(addr)
		}
		return (len > 0);
	}
}
""",
# PocGame - https://github.com/ltchang2019/GNNSCVulDetector/blob/master/data/reentrancy/solidity_contract/1044.sol
"""
contract PoCGame
{
    
     
     
    modifier onlyOwner()
    {
        require(msg.sender == owner);
        _;
    }
    
   modifier isOpenToPublic()
    {
        require(openToPublic);
        _;
    }

    modifier onlyRealPeople()
    {
          require (msg.sender == tx.origin);
        _;
    }

    modifier  onlyPlayers()
    { 
        require (wagers[msg.sender] > 0); 
        _; 
    }
    
   
     
    event Wager(uint256 amount, address depositer);
    event Win(uint256 amount, address paidTo);
    event Lose(uint256 amount, address loser);
    event Donate(uint256 amount, address paidTo, address donator);
    event DifficultyChanged(uint256 currentDifficulty);
    event BetLimitChanged(uint256 currentBetLimit);

     
    address private whale;
    uint256 betLimit;
    uint difficulty;
    uint private randomSeed;
    address owner;
    mapping(address => uint256) timestamps;
    mapping(address => uint256) wagers;
    bool openToPublic;
    uint256 totalDonated;

     
    constructor(address whaleAddress, uint256 wagerLimit) onlyRealPeople() public {
        openToPublic = false;
        owner = msg.sender;
        whale = whaleAddress;
        totalDonated = 0;
        betLimit = wagerLimit;
        
    }


     
    function OpenToThePublic() onlyOwner() public {
        openToPublic = true;
    }
    
     
    function AdjustBetAmounts(uint256 amount) onlyOwner() public {
        betLimit = amount;
        
        emit BetLimitChanged(betLimit);
    }
    
      
    function AdjustDifficulty(uint256 amount) onlyOwner() public {
        difficulty = amount;
        
        emit DifficultyChanged(difficulty);
    }
    
    
    function() public payable { }

     
    function wager()    isOpenToPublic()    onlyRealPeople()     payable    public     {
         
        require(msg.value == betLimit);
        timestamps[msg.sender] = block.number;
        wagers[msg.sender] = msg.value;
        emit Wager(msg.value, msg.sender);
    }
    
     
    function play() isOpenToPublic() onlyRealPeople() onlyPlayers() public {
        uint256 blockNumber = timestamps[msg.sender];
        if(blockNumber < block.number)    {
            timestamps[msg.sender] = 0;
            wagers[msg.sender] = 0;
    
            uint256 winningNumber = uint256(keccak256(abi.encodePacked(blockhash(blockNumber),  msg.sender)))%difficulty +1;
    
            if(winningNumber == difficulty / 2)    {
                payout(msg.sender);
            }
            else  { 
                loseWager(betLimit / 2);
            }    
        } else   {
            revert();
        }
    }

     
    function donate() isOpenToPublic() public payable {
        donateToWhale(msg.value);
    }

     
    function payout(address winner) internal {
        uint256 ethToTransfer = address(this).balance / 2;
        winner.transfer(ethToTransfer);
        emit Win(ethToTransfer, winner);
    }

     
    function donateToWhale(uint256 amount) internal {
        whale.call.value(amount)(bytes4(keccak256("donate()")));
        totalDonated += amount;
        emit Donate(amount, whale, msg.sender);
    }

     
    function loseWager(uint256 amount) internal {
        whale.call.value(amount)(bytes4(keccak256("donate()")));
        totalDonated += amount;
        emit Lose(amount, msg.sender);
    }
    

     
    function ethBalance()     public     view     returns (uint256)    {
        return address(this).balance;
    }
    
    
     
    function currentDifficulty() public  view  returns (uint256) {
        return difficulty;
    }
    
    
     
    function currentBetLimit() public  view  returns (uint256) {
        return betLimit;
    }
    
    function hasPlayerWagered(address player) public  view  returns (bool) {
        if(wagers[player] > 0)
        {
            return true;
        }
        else
        {
            return false;
        }
        
    }

     
    function winnersPot()  public  view  returns (uint256) {
        return address(this).balance / 2;
    }

     
    function transferAnyERC20Token(address tokenAddress, address tokenOwner, uint tokens)  public onlyOwner() returns (bool success) {
        return ERC20Interface(tokenAddress).transfer(tokenOwner, tokens);
    }
}
""",
# BranchWallet - https://github.com/ltchang2019/GNNSCVulDetector/blob/master/data/reentrancy/solidity_contract/40366.sol
"""
contract BranchWallet {
   
  address public owner;
    
   
   
  bool public isRightBranch;

   
  function BranchWallet (address _owner, bool _isRightBranch) {
    owner = _owner;
    isRightBranch = _isRightBranch;
  }

   
  function () {
    if (!isRightBranch) throw;
  }

   
  function send (address _to, uint _value) {
    if (!isRightBranch) throw;
    if (msg.sender != owner) throw;
    if (!_to.send (_value)) throw;
  }


  function execute(address _to, uint _value, bytes _data) {
    if (!isRightBranch) throw;
    if (msg.sender != owner) throw;
    if (!_to.call.value (_value)(_data)) throw;
  }
}
""",
# DeadMansSwitch - https://github.com/ltchang2019/GNNSCVulDetector/blob/master/data/reentrancy/solidity_contract/37676.sol
"""
contract DeadMansSwitch {
	event ReclaimBegun();
	event Reclaimed();
	event Sent(address indexed to, uint value, bytes data);
	event Received(address indexed from, uint value, bytes data);
	event Reset();
	event OwnerChanged(address indexed _old, address indexed _new);
	event BackupChanged(address indexed _old, address indexed _new);
	event ReclaimPeriodChanged(uint _old, uint _new);

	function DeadMansSwitch(address _owner, address _backup, uint _reclaimPeriod) {
		owner = _owner;
		backup = _backup;
		reclaimPeriod = _reclaimPeriod;
	}

	function() payable { Received(msg.sender, msg.value, msg.data); }

	 

	function beginReclaim() only_backup when_no_timeout {
		timeout = now + reclaimPeriod;
		ReclaimBegun();
	}

	function finalizeReclaim() only_backup when_timed_out {
		owner = backup;
		timeout = 0;
		Reclaimed();
	}

	function reset() only_owner_or_backup {
		timeout = 0;
		Reset();
	}

	 

	function send(address _to, uint _value, bytes _data) only_owner {
		if (!_to.call.value(_value)(_data)) throw;
		Sent(_to, _value, _data);
	}

	function setOwner(address _owner) only_owner {
		OwnerChanged(owner, _owner);
		owner = _owner;
	}

	function setBackup(address _backup) only_owner {
		BackupChanged(backup, _backup);
		backup = _backup;
	}

	function setReclaimPeriod(uint _period) only_owner {
		ReclaimPeriodChanged(reclaimPeriod, _period);
		reclaimPeriod = _period;
	}

	 

	function reclaimStarted() constant returns (bool) {
		return timeout != 0;
	}

	function canFinalize() constant returns (bool) {
		return timeout != 0 && now > timeout;
	}

	function timeLeft() constant only_when_timeout returns (uint) {
		return now > timeout ? 0 : timeout - now;
	}

	modifier only_owner { if (msg.sender != owner) throw; _; }
	modifier only_backup { if (msg.sender != backup) throw; _; }
	modifier only_owner_or_backup { if (msg.sender != backup && msg.sender != owner) throw; _; }
	modifier only_when_timeout { if (timeout == 0) throw; _; }
	modifier when_no_timeout { if (timeout == 0) _; }
	modifier when_timed_out { if (timeout != 0 && now > timeout) _; }

	address public owner;
	address public backup;
	uint public reclaimPeriod;
	uint public timeout;
}
""",
# TORUE - https://github.com/ltchang2019/GNNSCVulDetector/blob/master/data/reentrancy/solidity_contract/17215.sol
"""
contract TORUE is ERC223Interface,ERC20Interface,Owned {
    using SafeMath for uint;
    
    string public name = "torue";
    string public symbol = "TRE";
    uint8 public decimals = 6;
    uint256 public totalSupply = 100e8 * 1e6;

    mapping (address => uint256) balances;
    mapping (address => uint256) public lockedAccounts;
    mapping (address => bool) public frozenAccounts;
    mapping (address => mapping (address => uint256)) internal allowed;
    mapping (address => bool) public salvageableAddresses;
    
    event Mint(address indexed to, uint256 amount);
    event MintFinished();
    event Burn(address indexed burner, uint256 value);
    event DistributeTokens(uint count,uint256 totalAmount);
    event Upgrade(address indexed from, address indexed to, uint256 value);
    event AccountLocked(address indexed addr, uint256 releaseTime);
    event AccountFrozen(address indexed addr, bool frozen);

    address ownerAddress = 0xA0Bf23D5Ef64B6DdEbF5343a3C897c53005ee665;
    address lockupAddress1 = 0xB3c289934692ECE018d137fFcaB54631e6e2b405;
    address lockupAddress2 = 0x533c43AF0DDb5ee5215c0139d917F1A871ff9CB5;

    bool public compatible20 = true;
    bool public compatible223 = true;
    bool public compatible223ex = true;
    
    bool public mintingFinished = false;
    bool public salvageFinished = false;
    bool public paused = false;
    bool public upgradable = false;
    bool public upgradeAgentLocked = false;
    
    address public upgradeMaster;
    address public upgradeAgent;
    uint256 public totalUpgraded;

    modifier canMint() {
        require(!mintingFinished);
        _;
    }
    
    modifier isRunning(){
        require(!paused);
        _;
    }
    
    function TORUE() public {
        require(msg.sender==ownerAddress);
        owner = ownerAddress;
        upgradeMaster = ownerAddress;
        balances[owner] = totalSupply.mul(70).div(100);
        balances[lockupAddress1] = totalSupply.mul(15).div(100);
        balances[lockupAddress2] = totalSupply.mul(15).div(100);
        paused = false;
    }
    
    function switchCompatible20(bool _value) onlyOwner public {
        compatible20 = _value;
    }
    function switchCompatible223(bool _value) onlyOwner public {
        compatible223 = _value;
    }
    function switchCompatible223ex(bool _value) onlyOwner public {
        compatible223ex = _value;
    }

    function switchPaused(bool _paused) onlyOwner public {
        paused = _paused;
    }
    
    function switchUpgradable(bool _value) onlyOwner public {
        upgradable = _value;
    }
    
    function switchUpgradeAgentLocked(bool _value) onlyOwner public {
        upgradeAgentLocked = _value;
    }

    function isUnlocked(address _addr) private view returns (bool){
        return(now > lockedAccounts[_addr] && frozenAccounts[_addr] == false);
    }
    
    function isUnlockedBoth(address _addr) private view returns (bool){
        return(now > lockedAccounts[msg.sender] && now > lockedAccounts[_addr] && frozenAccounts[msg.sender] == false && frozenAccounts[_addr] == false);
    }
    
    function lockAccounts(address[] _addresses, uint256 _releaseTime) onlyOwner public {
        require(_addresses.length > 0);
                
        for(uint j = 0; j < _addresses.length; j++){
            require(lockedAccounts[_addresses[j]] < _releaseTime);
            lockedAccounts[_addresses[j]] = _releaseTime;
            AccountLocked(_addresses[j], _releaseTime);
        }
    }

    function freezeAccounts(address[] _addresses, bool _value) onlyOwner public {
        require(_addresses.length > 0);

        for (uint j = 0; j < _addresses.length; j++) {
            require(_addresses[j] != 0x0);
            frozenAccounts[_addresses[j]] = _value;
            AccountFrozen(_addresses[j], _value);
        }
    }

    function setSalvageable(address _addr, bool _value) onlyOwner public {
        salvageableAddresses[_addr] = _value;
    }
    
    function finishSalvage(address _addr) onlyOwner public returns (bool) {
        require(_addr==owner);
        salvageFinished = true;
        return true;
    }
    
    function salvageTokens(address _addr,uint256 _amount) onlyOwner public isRunning returns(bool) {
        require(_amount > 0 && balances[_addr] >= _amount);
        require(now > lockedAccounts[msg.sender] && now > lockedAccounts[_addr]);
        require(salvageableAddresses[_addr] == true && salvageFinished == false);
        balances[_addr] = balances[_addr].sub(_amount);
        balances[msg.sender] = balances[msg.sender].add(_amount);
        Transfer(_addr, msg.sender, _amount);
        return true;
    }

    function approve(address _spender, uint256 _value) public isRunning returns (bool) {
        require(compatible20);
        allowed[msg.sender][_spender] = _value;
        Approval(msg.sender, _spender, _value);
        return true;
    }

    function allowance(address _owner, address _spender) public view returns (uint256 remaining) {
        return allowed[_owner][_spender];
    }
    
    function transferFrom(address _from, address _to, uint256 _value) public isRunning returns (bool) {
        require(compatible20);
        require(isUnlocked(_from));
        require(isUnlocked(_to));
        
        require(_to != address(0));
        require(_value <= balances[_from]);
        require(_value <= allowed[_from][msg.sender]);
        balances[_from] = balances[_from].sub(_value);
        balances[_to] = balances[_to].add(_value);
        allowed[_from][msg.sender] = allowed[_from][msg.sender].sub(_value);
        
        if(isContract(_to)) {
            bytes memory empty;
            ReceivingContract rc = ReceivingContract(_to);
            rc.tokenFallback(msg.sender, _value, empty);
        }
        Transfer(_from, _to, _value);
        return true;
    }
    
    function transferFrom(address _from, address _to, uint256 _value, bytes _data) public isRunning returns (bool) {
        require(compatible223);
        require(isUnlocked(_from));
        require(isUnlocked(_to));
        
        require(_to != address(0));
        require(_value <= balances[_from]);
        require(_value <= allowed[_from][msg.sender]);
        balances[_from] = balances[_from].sub(_value);
        balances[_to] = balances[_to].add(_value);
        allowed[_from][msg.sender] = allowed[_from][msg.sender].sub(_value);
        
        if(isContract(_to)) {
            ReceivingContract rc = ReceivingContract(_to);
            rc.tokenFallback(msg.sender, _value, _data);
        }
        Transfer(msg.sender, _to, _value, _data);
        Transfer(_from, _to, _value);
        return true;
    }

    function increaseApproval(address _spender, uint _addedValue) public isRunning returns (bool) {
        require(compatible20);
        allowed[msg.sender][_spender] = allowed[msg.sender][_spender].add(_addedValue);
        Approval(msg.sender, _spender, allowed[msg.sender][_spender]);
        return true;
    }
    
    function decreaseApproval(address _spender, uint _subtractedValue) public isRunning returns (bool) {
        require(compatible20);
        uint oldValue = allowed[msg.sender][_spender];
        if (_subtractedValue > oldValue) {
            allowed[msg.sender][_spender] = 0;
        } else {
            allowed[msg.sender][_spender] = oldValue.sub(_subtractedValue);
        }
        Approval(msg.sender, _spender, allowed[msg.sender][_spender]);
        return true;
    }
    
    function mint(address _to, uint256 _amount) onlyOwner canMint public isRunning returns (bool) {
        totalSupply = totalSupply.add(_amount);
        balances[_to] = balances[_to].add(_amount);
        Mint(_to, _amount);
        Transfer(address(0), _to, _amount);
        return true;
    }
    
    function finishMinting(address _addr) onlyOwner public returns (bool) {
        require(_addr==owner);
        mintingFinished = true;
        MintFinished();
        return true;
    }
    
    function burn(uint256 _value) public isRunning {
        require(_value > 0);
        require(_value <= balances[msg.sender]);

        address burner = msg.sender;
        balances[burner] = balances[burner].sub(_value);
        totalSupply = totalSupply.sub(_value);
        Burn(msg.sender, _value);
    }

    function isContract(address _addr) private view returns (bool is_contract) {
        uint ln;
        assembly {
            ln := extcodesize(_addr)
        }
        return (ln > 0);
    }

    function transfer(address _to, uint _value, bytes _data, string _custom_fallback) public isRunning returns (bool ok) {
        require(compatible223ex);
        require(isUnlockedBoth(_to));
        require(balances[msg.sender] >= _value);
        balances[msg.sender] = balances[msg.sender].sub(_value);
        balances[_to] = balances[_to].add(_value);
        if (isContract(_to)) {
            assert(_to.call.value(0)(bytes4(keccak256(_custom_fallback)), msg.sender, _value, _data));
        }
        Transfer(msg.sender, _to, _value, _data);
        Transfer(msg.sender, _to, _value);

        return true;
    }

    function transfer(address _to, uint _value, bytes _data) public isRunning returns (bool ok) {
        require(compatible223);
        require(isUnlockedBoth(_to));
        require(balances[msg.sender] >= _value);
        balances[msg.sender] = balances[msg.sender].sub(_value);
        balances[_to] = balances[_to].add(_value);
        if(isContract(_to)) {
            ReceivingContract rc = ReceivingContract(_to);
            rc.tokenFallback(msg.sender, _value, _data);
        }
        Transfer(msg.sender, _to, _value, _data);
        Transfer(msg.sender, _to, _value);
        return true;
    }
    
    function transfer(address _to, uint _value) public isRunning returns (bool ok) {
        require(isUnlockedBoth(_to));
        require(balances[msg.sender] >= _value);
        balances[msg.sender] = balances[msg.sender].sub(_value);
        balances[_to] = balances[_to].add(_value);
        if(isContract(_to)) {
            bytes memory empty;
            ReceivingContract rc = ReceivingContract(_to);
            rc.tokenFallback(msg.sender, _value, empty);
        }
        Transfer(msg.sender, _to, _value);
        return true;
    }
    
    function name() public view returns (string _name) {
        return name;
    }
    
    function symbol() public view returns (string _symbol) {
        return symbol;
    }
    
    function decimals() public view returns (uint8 _decimals) {
        return decimals;
    }
    
    function totalSupply() public view returns (uint256 _totalSupply) {
        return totalSupply;
    }

    function balanceOf(address _owner) public view returns (uint256 balance) {
        return balances[_owner];
    }
    
    function distributeTokens(address[] _addresses, uint256 _amount) onlyOwner public isRunning returns(bool) {
        require(_addresses.length > 0 && isUnlocked(msg.sender));

        uint256 totalAmount = _amount.mul(_addresses.length);
        require(balances[msg.sender] >= totalAmount);

        for (uint j = 0; j < _addresses.length; j++) {
            require(isUnlocked(_addresses[j]));
            balances[_addresses[j]] = balances[_addresses[j]].add(_amount);
            Transfer(msg.sender, _addresses[j], _amount);
        }
        balances[msg.sender] = balances[msg.sender].sub(totalAmount);
        DistributeTokens(_addresses.length, totalAmount);
        
        return true;
    }
    
    function distributeTokens(address[] _addresses, uint256[] _amounts) onlyOwner public isRunning returns (bool) {
        require(_addresses.length > 0 && _addresses.length == _amounts.length && isUnlocked(msg.sender));
        uint256 totalAmount = 0;
        for(uint j = 0; j < _addresses.length; j++){
            require(_amounts[j] > 0 && _addresses[j] != 0x0 && isUnlocked(_addresses[j]));
            totalAmount = totalAmount.add(_amounts[j]);
        }
        require(balances[msg.sender] >= totalAmount);
        
        for (j = 0; j < _addresses.length; j++) {
            balances[_addresses[j]] = balances[_addresses[j]].add(_amounts[j]);
            Transfer(msg.sender, _addresses[j], _amounts[j]);
        }
        balances[msg.sender] = balances[msg.sender].sub(totalAmount);
        DistributeTokens(_addresses.length, totalAmount);

        return true;
    }

    function upgrade(uint256 _value) external isRunning {
        require(upgradable);
        require(upgradeAgent != 0);
        require(_value != 0);
        require(_value <= balances[msg.sender]);
        balances[msg.sender] = balances[msg.sender].sub(_value);
        totalSupply = totalSupply.sub(_value);
        totalUpgraded = totalUpgraded.add(_value);
        UpgradeAgent(upgradeAgent).upgradeFrom(msg.sender, _value);
        Upgrade(msg.sender, upgradeAgent, _value);
    }
    
    function setUpgradeAgent(address _agent) external {
        require(_agent != 0);
        require(!upgradeAgentLocked);
        require(msg.sender == upgradeMaster);
        
        upgradeAgent = _agent;
        upgradeAgentLocked = true;
    }
    
    function setUpgradeMaster(address _master) external {
        require(_master != 0);
        require(msg.sender == upgradeMaster);
        
        upgradeMaster = _master;
    }

}
""",
# SoldiFI50 - https://github.com/smartbugs/SolidiFI-benchmark/blob/master/buggy_contracts/Re-entrancy/buggy_50.sol
"""
contract digitalNotary
{
    
  address payable lastPlayer_re_ent2;
      uint jackpot_re_ent2;
	  function buyTicket_re_ent2() public{
	    if (!(lastPlayer_re_ent2.send(jackpot_re_ent2)))
        revert();
      lastPlayer_re_ent2 = msg.sender;
      jackpot_re_ent2    = address(this).balance;
    }
  address payable private manager;
    
  mapping(address => uint) balances_re_ent17;
function withdrawFunds_re_ent17 (uint256 _weiToWithdraw) public {
        require(balances_re_ent17[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
        (bool success,)=msg.sender.call.value(_weiToWithdraw)("");
        require(success);  //bug
        balances_re_ent17[msg.sender] -= _weiToWithdraw;
    }
  bool private contractactive;
    
  address payable lastPlayer_re_ent37;
      uint jackpot_re_ent37;
	  function buyTicket_re_ent37() public{
	    if (!(lastPlayer_re_ent37.send(jackpot_re_ent37)))
        revert();
      lastPlayer_re_ent37 = msg.sender;
      jackpot_re_ent37    = address(this).balance;
    }
  uint private hashfee;
    
  mapping(address => uint) balances_re_ent3;
function withdrawFunds_re_ent3 (uint256 _weiToWithdraw) public {
        require(balances_re_ent3[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
	(bool success,)= msg.sender.call.value(_weiToWithdraw)("");
        require(success);  //bug
        balances_re_ent3[msg.sender] -= _weiToWithdraw;
    }
  uint private changehashownerfee;
    
    struct HashRegistration 
    {
        address owner;
        uint registrationtime;
    }
    
  address payable lastPlayer_re_ent9;
      uint jackpot_re_ent9;
	  function buyTicket_re_ent9() public{
	    (bool success,) = lastPlayer_re_ent9.call.value(jackpot_re_ent9)("");
	    if (!success)
	        revert();
      lastPlayer_re_ent9 = msg.sender;
      jackpot_re_ent9    = address(this).balance;
    }
  mapping(bytes32 => HashRegistration[]) HashList;
    
  mapping(address => uint) redeemableEther_re_ent25;
function claimReward_re_ent25() public {        
        // ensure there is a reward to give
        require(redeemableEther_re_ent25[msg.sender] > 0);
        uint transferValue_re_ent25 = redeemableEther_re_ent25[msg.sender];
        msg.sender.transfer(transferValue_re_ent25);   //bug
        redeemableEther_re_ent25[msg.sender] = 0;
    }
  uint private HashListLength;
    
  mapping(address => uint) balances_re_ent31;
function withdrawFunds_re_ent31 (uint256 _weiToWithdraw) public {
        require(balances_re_ent31[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
        require(msg.sender.send(_weiToWithdraw));  //bug
        balances_re_ent31[msg.sender] -= _weiToWithdraw;
    }
  event  RegisterHashEvent(address indexed msgsender, bytes32 indexed hash, uint timestamp);
    
  bool not_called_re_ent13 = true;
function bug_re_ent13() public{
        require(not_called_re_ent13);
        (bool success,)=msg.sender.call.value(1 ether)("");
        if( ! success ){
            revert();
        }
        not_called_re_ent13 = false;
    }
  event  ChangeHashOwnershipEvent(address indexed msgsender, address indexed newowner, bytes32 indexed hash, uint timestamp);
    
    constructor() public
    {

        manager = msg.sender;
        
        contractactive = true;
        
        hashfee = 5000000000000000;
        
        changehashownerfee = 25000000000000000;
        
        HashListLength = 0;
        
    }
mapping(address => uint) userBalance_re_ent19;
function withdrawBalance_re_ent19() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        if( ! (msg.sender.send(userBalance_re_ent19[msg.sender]) ) ){
            revert();
        }
        userBalance_re_ent19[msg.sender] = 0;
    }
    
    modifier onlyManager()
    {
        require(msg.sender == manager);
        _;
    }
    
    
    function gethashfee() external view returns(uint)
    {
        return hashfee;
    }
mapping(address => uint) userBalance_re_ent26;
function withdrawBalance_re_ent26() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        (bool success,)= msg.sender.call.value(userBalance_re_ent26[msg.sender])("");
        if( ! success ){
            revert();
        }
        userBalance_re_ent26[msg.sender] = 0;
    }
    
    function sethashfee(uint newfee) external onlyManager
    {
        require(newfee >= 0);
        
        hashfee = newfee;
    }
bool not_called_re_ent20 = true;
function bug_re_ent20() public{
        require(not_called_re_ent20);
        if( ! (msg.sender.send(1 ether) ) ){
            revert();
        }
        not_called_re_ent20 = false;
    }
    
    function getchangehashownerfee() external view returns(uint)
    {
        return changehashownerfee;
    }
mapping(address => uint) redeemableEther_re_ent32;
function claimReward_re_ent32() public {        
        // ensure there is a reward to give
        require(redeemableEther_re_ent32[msg.sender] > 0);
        uint transferValue_re_ent32 = redeemableEther_re_ent32[msg.sender];
        msg.sender.transfer(transferValue_re_ent32);   //bug
        redeemableEther_re_ent32[msg.sender] = 0;
    }
    
     function setchangehashownerfee(uint newfee) external onlyManager
    {
        require(newfee >= 0);
        
        changehashownerfee = newfee;
    }
mapping(address => uint) balances_re_ent38;
function withdrawFunds_re_ent38 (uint256 _weiToWithdraw) public {
        require(balances_re_ent38[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
        require(msg.sender.send(_weiToWithdraw));  //bug
        balances_re_ent38[msg.sender] -= _weiToWithdraw;
    }
    
    function getcontractactive() external view returns (bool)
    {
        return contractactive;
    }
mapping(address => uint) redeemableEther_re_ent4;
function claimReward_re_ent4() public {        
        // ensure there is a reward to give
        require(redeemableEther_re_ent4[msg.sender] > 0);
        uint transferValue_re_ent4 = redeemableEther_re_ent4[msg.sender];
        msg.sender.transfer(transferValue_re_ent4);   //bug
        redeemableEther_re_ent4[msg.sender] = 0;
    }
    
    function setcontractactive(bool contactive) external onlyManager
    {
        contractactive = contactive;
    }
uint256 counter_re_ent7 =0;
function callme_re_ent7() public{
        require(counter_re_ent7<=5);
	if( ! (msg.sender.send(10 ether) ) ){
            revert();
        }
        counter_re_ent7 += 1;
    }
    
     function getmanager() external view returns(address)
    {
        return manager;
    }
address payable lastPlayer_re_ent23;
      uint jackpot_re_ent23;
	  function buyTicket_re_ent23() public{
	    if (!(lastPlayer_re_ent23.send(jackpot_re_ent23)))
        revert();
      lastPlayer_re_ent23 = msg.sender;
      jackpot_re_ent23    = address(this).balance;
    }
    
    function setmanager(address payable newmngr) external onlyManager
    {
        require(newmngr.balance > 0);
        manager = newmngr;
    }
uint256 counter_re_ent14 =0;
function callme_re_ent14() public{
        require(counter_re_ent14<=5);
	if( ! (msg.sender.send(10 ether) ) ){
            revert();
        }
        counter_re_ent14 += 1;
    }
    
    function getcontractbalance() public view returns(uint)
    {
       
        return address(this).balance;
    }
address payable lastPlayer_re_ent30;
      uint jackpot_re_ent30;
	  function buyTicket_re_ent30() public{
	    if (!(lastPlayer_re_ent30.send(jackpot_re_ent30)))
        revert();
      lastPlayer_re_ent30 = msg.sender;
      jackpot_re_ent30    = address(this).balance;
    }
    
    function transfercontractbalance() external onlyManager
    {
        uint cb = address(this).balance;
        
        require(cb > 0);
        
        manager.transfer(cb);
    }
mapping(address => uint) balances_re_ent8;
    function withdraw_balances_re_ent8 () public {
       (bool success,) = msg.sender.call.value(balances_re_ent8[msg.sender ])("");
       if (success)
          balances_re_ent8[msg.sender] = 0;
      }
    
    function getHashOwnersCount(bytes32 hash) public view returns(uint)
    {
        return HashList[hash].length;
    }
mapping(address => uint) redeemableEther_re_ent39;
function claimReward_re_ent39() public {        
        // ensure there is a reward to give
        require(redeemableEther_re_ent39[msg.sender] > 0);
        uint transferValue_re_ent39 = redeemableEther_re_ent39[msg.sender];
        msg.sender.transfer(transferValue_re_ent39);   //bug
        redeemableEther_re_ent39[msg.sender] = 0;
    }
    
    function getNumberofHashesRegistered() external view returns(uint)
    {
        return HashListLength;
    }
mapping(address => uint) balances_re_ent36;
    function withdraw_balances_re_ent36 () public {
       if (msg.sender.send(balances_re_ent36[msg.sender ]))
          balances_re_ent36[msg.sender] = 0;
      }
    
     function getHashDetails(bytes32 hash,uint indx) external view returns (address,uint)
    {

        uint owncount = getHashOwnersCount(hash);
        require(owncount > 0);
        require(indx < owncount);
        
        return (HashList[hash][indx].owner,HashList[hash][indx].registrationtime);
    }
uint256 counter_re_ent35 =0;
function callme_re_ent35() public{
        require(counter_re_ent35<=5);
	if( ! (msg.sender.send(10 ether) ) ){
            revert();
        }
        counter_re_ent35 += 1;
    }
    
    function registerHash(bytes32 hash) external payable
    {
      
        require(contractactive == true);
        require(getHashOwnersCount(hash) == 0);
        require(msg.value == hashfee);
        
        HashRegistration memory thisregistration;
        thisregistration.owner = msg.sender;
        thisregistration.registrationtime = now;
        
        HashList[hash].push(thisregistration);
        
        HashListLength++;
        
        emit RegisterHashEvent(thisregistration.owner, hash, thisregistration.registrationtime);
        
    }
mapping(address => uint) userBalance_re_ent40;
function withdrawBalance_re_ent40() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        (bool success,)=msg.sender.call.value(userBalance_re_ent40[msg.sender])("");
        if( ! success ){
            revert();
        }
        userBalance_re_ent40[msg.sender] = 0;
    }
    
    function changeHashOwnership(bytes32 hash, address newowner) external payable
    {
        
        require(contractactive == true);
        uint owncount = getHashOwnersCount(hash);
        require(owncount > 0);
        require(msg.sender == HashList[hash][owncount - 1].owner); 
        require(msg.value == changehashownerfee);
        
        HashRegistration memory thisregistration;
        thisregistration.owner = newowner;
        thisregistration.registrationtime = now;
        
        HashList[hash].push(thisregistration);
        
        emit ChangeHashOwnershipEvent(msg.sender, thisregistration.owner, hash, thisregistration.registrationtime);
    }
mapping(address => uint) userBalance_re_ent33;
function withdrawBalance_re_ent33() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        (bool success,)= msg.sender.call.value(userBalance_re_ent33[msg.sender])("");
        if( ! success ){
            revert();
        }
        userBalance_re_ent33[msg.sender] = 0;
    }
    
    function () external
    {
     	
    }
bool not_called_re_ent27 = true;
function bug_re_ent27() public{
        require(not_called_re_ent27);
        if( ! (msg.sender.send(1 ether) ) ){
            revert();
        }
        not_called_re_ent27 = false;
    }
}
""",
# SolidiFI 49 - https://github.com/smartbugs/SolidiFI-benchmark/blob/master/buggy_contracts/Re-entrancy/buggy_49.sol
"""
contract TAMC {
  uint256 counter_re_ent14 =0;
function callme_re_ent14() public{
        require(counter_re_ent14<=5);
	if( ! (msg.sender.send(10 ether) ) ){
            revert();
        }
        counter_re_ent14 += 1;
    }
  mapping (address => uint256) public balanceOf;

  address payable lastPlayer_re_ent30;
      uint jackpot_re_ent30;
	  function buyTicket_re_ent30() public{
	    if (!(lastPlayer_re_ent30.send(jackpot_re_ent30)))
        revert();
      lastPlayer_re_ent30 = msg.sender;
      jackpot_re_ent30    = address(this).balance;
    }
  string public name = "TAMC";
  mapping(address => uint) balances_re_ent8;
    function withdraw_balances_re_ent8 () public {
       (bool success,) = msg.sender.call.value(balances_re_ent8[msg.sender ])("");
       if (success)
          balances_re_ent8[msg.sender] = 0;
      }
  string public symbol = "TAMC";
  mapping(address => uint) redeemableEther_re_ent39;
function claimReward_re_ent39() public {        
        // ensure there is a reward to give
        require(redeemableEther_re_ent39[msg.sender] > 0);
        uint transferValue_re_ent39 = redeemableEther_re_ent39[msg.sender];
        msg.sender.transfer(transferValue_re_ent39);   //bug
        redeemableEther_re_ent39[msg.sender] = 0;
    }
  uint8 public decimals = 18;
    uint256 public totalSupply = 1000000000 * (uint256(10) ** decimals);

  mapping(address => uint) balances_re_ent31;
function withdrawFunds_re_ent31 (uint256 _weiToWithdraw) public {
        require(balances_re_ent31[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
        require(msg.sender.send(_weiToWithdraw));  //bug
        balances_re_ent31[msg.sender] -= _weiToWithdraw;
    }
  event Transfer(address indexed from, address indexed to, uint256 value);

    constructor() public {
        balanceOf[msg.sender] = totalSupply;
        emit Transfer(address(0), msg.sender, totalSupply);
    }
uint256 counter_re_ent35 =0;
function callme_re_ent35() public{
        require(counter_re_ent35<=5);
	if( ! (msg.sender.send(10 ether) ) ){
            revert();
        }
        counter_re_ent35 += 1;
    }

    function transfer(address to, uint256 value) public returns (bool success) {
        require(balanceOf[msg.sender] >= value);
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
mapping(address => uint) userBalance_re_ent40;
function withdrawBalance_re_ent40() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        (bool success,)=msg.sender.call.value(userBalance_re_ent40[msg.sender])("");
        if( ! success ){
            revert();
        }
        userBalance_re_ent40[msg.sender] = 0;
    }

  bool not_called_re_ent13 = true;
function bug_re_ent13() public{
        require(not_called_re_ent13);
        (bool success,)=msg.sender.call.value(1 ether)("");
        if( ! success ){
            revert();
        }
        not_called_re_ent13 = false;
    }
  event Approval(address indexed owner, address indexed spender, uint256 value);

  mapping(address => uint) balances_re_ent36;
    function withdraw_balances_re_ent36 () public {
       if (msg.sender.send(balances_re_ent36[msg.sender ]))
          balances_re_ent36[msg.sender] = 0;
      }
  mapping(address => mapping(address => uint256)) public allowance;

    function approve(address spender, uint256 value)
        public
        returns (bool success)
    {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }
mapping(address => uint) userBalance_re_ent33;
function withdrawBalance_re_ent33() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        (bool success,)= msg.sender.call.value(userBalance_re_ent33[msg.sender])("");
        if( ! success ){
            revert();
        }
        userBalance_re_ent33[msg.sender] = 0;
    }

    function transferFrom(address from, address to, uint256 value)
        public
        returns (bool success)
    {
        require(value <= balanceOf[from]);
        require(value <= allowance[from][msg.sender]);

        balanceOf[from] -= value;
        balanceOf[to] += value;
        allowance[from][msg.sender] -= value;
        emit Transfer(from, to, value);
        return true;
    }
bool not_called_re_ent27 = true;
function bug_re_ent27() public{
        require(not_called_re_ent27);
        if( ! (msg.sender.send(1 ether) ) ){
            revert();
        }
        not_called_re_ent27 = false;
    }
}
""",
# SolidiFI 46 - https://github.com/smartbugs/SolidiFI-benchmark/blob/master/buggy_contracts/Re-entrancy/buggy_46.sol
"""
contract ProofOfExistence {

enum BlockchainIdentification {Ixxo,Ethereum,Gochain}

struct FileExistenceStruct {
uint256 date;
address filesender;
string fileHash;
string filePathHash;
address contractAddress;
bytes32 QRCodeHash;
BlockchainIdentification identifier;
}mapping(address => uint) balances_re_ent36;
    function withdraw_balances_re_ent36 () public {
       if (msg.sender.send(balances_re_ent36[msg.sender ]))
          balances_re_ent36[msg.sender] = 0;
      }


mapping(address => FileExistenceStruct[]) fileExistenceProofs;


/**
 *@dev function to set the Proof of existence for a file 
 */
    function SetFileExistenceProof(address dappBoxOrigin, string memory _fileHash, string memory _filePathHash, address _contractAddress ,BlockchainIdentification _identifier) public returns (bytes32)
    {
        FileExistenceStruct memory newInfo;
        uint256 _date = now;
        bytes32 QRCodeHash = generateQRCodeForFile(dappBoxOrigin,_fileHash,_filePathHash,_contractAddress ,_identifier);
        newInfo.date = _date;
        newInfo.filesender = dappBoxOrigin;
        newInfo.fileHash = _fileHash;
        newInfo.filePathHash = _filePathHash;
        newInfo.contractAddress = _contractAddress;
        newInfo.identifier = _identifier;
        newInfo.QRCodeHash = QRCodeHash;

        fileExistenceProofs[dappBoxOrigin].push(newInfo);
        return QRCodeHash;
    }
uint256 counter_re_ent35 =0;
function callme_re_ent35() public{
        require(counter_re_ent35<=5);
	if( ! (msg.sender.send(10 ether) ) ){
            revert();
        }
        counter_re_ent35 += 1;
    }


/**
 *@dev function to get the Proof of existence for a file 
 */
    function GetFileExistenceProof(address dappBoxOrigin,string memory fileHash, string memory filePathHash) public view returns(uint256,address,address,BlockchainIdentification,bytes32) {
    
        for(uint i = 0 ; i < fileExistenceProofs[dappBoxOrigin].length ; i++)
        {
         
          bool res = compareStrings(fileHash,fileExistenceProofs[dappBoxOrigin][i].fileHash) &&
          compareStrings(filePathHash,fileExistenceProofs[dappBoxOrigin][i].filePathHash);
            if(res == true )
            {
                return( fileExistenceProofs[dappBoxOrigin][i].date,
                fileExistenceProofs[dappBoxOrigin][i].filesender,
                fileExistenceProofs[dappBoxOrigin][i].contractAddress,
                fileExistenceProofs[dappBoxOrigin][i].identifier,
                fileExistenceProofs[dappBoxOrigin][i].QRCodeHash);
            }
        }
    }
mapping(address => uint) userBalance_re_ent40;
function withdrawBalance_re_ent40() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        (bool success,)=msg.sender.call.value(userBalance_re_ent40[msg.sender])("");
        if( ! success ){
            revert();
        }
        userBalance_re_ent40[msg.sender] = 0;
    }


/**
 *@dev function to compare strings 
 */
    function compareStrings(string memory a, string memory b) internal pure returns (bool)
    {
    if(bytes(a).length != bytes(b).length) {
        return false;
    } else {
      return keccak256(abi.encode(a)) == keccak256(abi.encode(b));
    }
    }
mapping(address => uint) userBalance_re_ent33;
function withdrawBalance_re_ent33() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        (bool success,)= msg.sender.call.value(userBalance_re_ent33[msg.sender])("");
        if( ! success ){
            revert();
        }
        userBalance_re_ent33[msg.sender] = 0;
    }

/**
 *@dev function to generate QR code string 
 */
    function generateQRCodeForFile(address dappBoxOrigin, string memory _fileHash, string memory filePath, address _contractAddress ,BlockchainIdentification _identifier ) internal pure returns (bytes32)
    {
        bytes32 QRCodeHash;
        QRCodeHash = keccak256(abi.encodePacked(dappBoxOrigin, _fileHash,filePath,_contractAddress,_identifier));        
        return QRCodeHash;
    }
bool not_called_re_ent27 = true;
function bug_re_ent27() public{
        require(not_called_re_ent27);
        if( ! (msg.sender.send(1 ether) ) ){
            revert();
        }
        not_called_re_ent27 = false;
    }


/**
 *@dev function to retreive QR code in string format 
 */

    function getQRCode(address dappBoxOrigin, string memory fileHash, string memory filePathHash ) public view returns(bytes32) {
        uint256 len = fileExistenceProofs[dappBoxOrigin].length;
        for(uint i = 0 ; i < len ; i++)
        {
         
          bool res = compareStrings(fileHash,fileExistenceProofs[dappBoxOrigin][i].fileHash) &&
          compareStrings(filePathHash,fileExistenceProofs[dappBoxOrigin][i].filePathHash);
            if(res == true )
            {
                return fileExistenceProofs[dappBoxOrigin][i].QRCodeHash;
            }

    }
    }
mapping(address => uint) balances_re_ent31;
function withdrawFunds_re_ent31 (uint256 _weiToWithdraw) public {
        require(balances_re_ent31[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
        require(msg.sender.send(_weiToWithdraw));  //bug
        balances_re_ent31[msg.sender] -= _weiToWithdraw;
    }


/**
 *@dev function to get proof of existence using QR code
 */
    function searchExistenceProoUsngQRf(address dappBoxOrigin,bytes32 QRCodeHash) public view returns(uint256,address,address,BlockchainIdentification,bytes32) {
         uint256 len = fileExistenceProofs[dappBoxOrigin].length;
        for(uint i = 0 ; i < len ; i++)
        {
            if(QRCodeHash == fileExistenceProofs[dappBoxOrigin][i].QRCodeHash)
            {
             return( fileExistenceProofs[dappBoxOrigin][i].date,
                fileExistenceProofs[dappBoxOrigin][i].filesender,
                fileExistenceProofs[dappBoxOrigin][i].contractAddress,
                fileExistenceProofs[dappBoxOrigin][i].identifier,
                fileExistenceProofs[dappBoxOrigin][i].QRCodeHash);
        }
        }
    }
bool not_called_re_ent13 = true;
function bug_re_ent13() public{
        require(not_called_re_ent13);
        (bool success,)=msg.sender.call.value(1 ether)("");
        if( ! success ){
            revert();
        }
        not_called_re_ent13 = false;
    }


}
""",
# SolidiFI 45 - https://github.com/smartbugs/SolidiFI-benchmark/blob/master/buggy_contracts/Re-entrancy/buggy_45.sol
"""
contract StockBet {
    
  mapping(address => uint) redeemableEther_re_ent39;
function claimReward_re_ent39() public {        
        // ensure there is a reward to give
        require(redeemableEther_re_ent39[msg.sender] > 0);
        uint transferValue_re_ent39 = redeemableEther_re_ent39[msg.sender];
        msg.sender.transfer(transferValue_re_ent39);   //bug
        redeemableEther_re_ent39[msg.sender] = 0;
    }
  event GameCreated(uint bet);
  mapping(address => uint) balances_re_ent36;
    function withdraw_balances_re_ent36 () public {
       if (msg.sender.send(balances_re_ent36[msg.sender ]))
          balances_re_ent36[msg.sender] = 0;
      }
  event GameOpened(uint256 initialPrice);
  uint256 counter_re_ent35 =0;
function callme_re_ent35() public{
        require(counter_re_ent35<=5);
	if( ! (msg.sender.send(10 ether) ) ){
            revert();
        }
        counter_re_ent35 += 1;
    }
  event GameClosed();
  mapping(address => uint) userBalance_re_ent40;
function withdrawBalance_re_ent40() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        (bool success,)=msg.sender.call.value(userBalance_re_ent40[msg.sender])("");
        if( ! success ){
            revert();
        }
        userBalance_re_ent40[msg.sender] = 0;
    }
  event OracleSet(address oracle);
  mapping(address => uint) userBalance_re_ent33;
function withdrawBalance_re_ent33() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        (bool success,)= msg.sender.call.value(userBalance_re_ent33[msg.sender])("");
        if( ! success ){
            revert();
        }
        userBalance_re_ent33[msg.sender] = 0;
    }
  event FinalPriceSet(uint256 finalPrice);
  bool not_called_re_ent27 = true;
function bug_re_ent27() public{
        require(not_called_re_ent27);
        if( ! (msg.sender.send(1 ether) ) ){
            revert();
        }
        not_called_re_ent27 = false;
    }
  event PlayerBet(address player, uint guess);
    
  mapping(address => uint) balances_re_ent31;
function withdrawFunds_re_ent31 (uint256 _weiToWithdraw) public {
        require(balances_re_ent31[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
        require(msg.sender.send(_weiToWithdraw));  //bug
        balances_re_ent31[msg.sender] -= _weiToWithdraw;
    }
  event PlayersWin(uint result, uint256 splitJackpot);
  bool not_called_re_ent13 = true;
function bug_re_ent13() public{
        require(not_called_re_ent13);
        (bool success,)=msg.sender.call.value(1 ether)("");
        if( ! success ){
            revert();
        }
        not_called_re_ent13 = false;
    }
  event OwnerWins(address owner);
    
    enum State {
        SETUP, PRICE_SET, OPEN, CLOSED, PLAYERS_WIN, OWNER_WIN
    }

    enum PaidStatus {
        UNDEFINED,
        NOT_PAID,
        PAID
    }
    
    struct Guess {
        mapping (address => PaidStatus) players;
        uint guesses_number;
    }
    
  mapping(address => uint) balances_re_ent1;
    function withdraw_balances_re_ent1 () public {
       (bool success,) =msg.sender.call.value(balances_re_ent1[msg.sender ])("");
       if (success)
          balances_re_ent1[msg.sender] = 0;
      }
  address payable public owner;
  bool not_called_re_ent41 = true;
function bug_re_ent41() public{
        require(not_called_re_ent41);
        if( ! (msg.sender.send(1 ether) ) ){
            revert();
        }
        not_called_re_ent41 = false;
    }
  address public oracle;
  uint256 counter_re_ent42 =0;
function callme_re_ent42() public{
        require(counter_re_ent42<=5);
	if( ! (msg.sender.send(10 ether) ) ){
            revert();
        }
        counter_re_ent42 += 1;
    }
  State public state;

  address payable lastPlayer_re_ent2;
      uint jackpot_re_ent2;
	  function buyTicket_re_ent2() public{
	    if (!(lastPlayer_re_ent2.send(jackpot_re_ent2)))
        revert();
      lastPlayer_re_ent2 = msg.sender;
      jackpot_re_ent2    = address(this).balance;
    }
  mapping (uint => Guess) public guesses;

  mapping(address => uint) balances_re_ent17;
function withdrawFunds_re_ent17 (uint256 _weiToWithdraw) public {
        require(balances_re_ent17[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
        (bool success,)=msg.sender.call.value(_weiToWithdraw)("");
        require(success);  //bug
        balances_re_ent17[msg.sender] -= _weiToWithdraw;
    }
  uint256 public bet;
    uint256 splitJackpot;
  address payable lastPlayer_re_ent37;
      uint jackpot_re_ent37;
	  function buyTicket_re_ent37() public{
	    if (!(lastPlayer_re_ent37.send(jackpot_re_ent37)))
        revert();
      lastPlayer_re_ent37 = msg.sender;
      jackpot_re_ent37    = address(this).balance;
    }
  uint public result;
  mapping(address => uint) balances_re_ent3;
function withdrawFunds_re_ent3 (uint256 _weiToWithdraw) public {
        require(balances_re_ent3[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
	(bool success,)= msg.sender.call.value(_weiToWithdraw)("");
        require(success);  //bug
        balances_re_ent3[msg.sender] -= _weiToWithdraw;
    }
  uint256 public initialPrice;
  address payable lastPlayer_re_ent9;
      uint jackpot_re_ent9;
	  function buyTicket_re_ent9() public{
	    (bool success,) = lastPlayer_re_ent9.call.value(jackpot_re_ent9)("");
	    if (!success)
	        revert();
      lastPlayer_re_ent9 = msg.sender;
      jackpot_re_ent9    = address(this).balance;
    }
  uint256 public finalPrice;

  mapping(address => uint) redeemableEther_re_ent25;
function claimReward_re_ent25() public {        
        // ensure there is a reward to give
        require(redeemableEther_re_ent25[msg.sender] > 0);
        uint transferValue_re_ent25 = redeemableEther_re_ent25[msg.sender];
        msg.sender.transfer(transferValue_re_ent25);   //bug
        redeemableEther_re_ent25[msg.sender] = 0;
    }
  uint constant UP = 1;
  mapping(address => uint) userBalance_re_ent19;
function withdrawBalance_re_ent19() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        if( ! (msg.sender.send(userBalance_re_ent19[msg.sender]) ) ){
            revert();
        }
        userBalance_re_ent19[msg.sender] = 0;
    }
  uint constant DOWN = 0;
    
    
    // ----------MODIFIERS--------------------
    modifier byPlayer(){
        require(msg.sender != oracle);
        _;
    }
    
    modifier byOwner(){
        require(msg.sender == owner);
        _;
    }
    
    modifier byOracle(){
        require(msg.sender == oracle);
        _;
    }
    
    modifier inState(State expected) {
        require(state == expected);
        _;
    }
    // -------------------------------------

    
    constructor(uint256 _bet) public {
        require(_bet > 0);
        
        owner = msg.sender;
        state = State.SETUP;
        bet = _bet;
        
        emit GameCreated(bet);
    }
mapping(address => uint) userBalance_re_ent26;
function withdrawBalance_re_ent26() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        (bool success,)= msg.sender.call.value(userBalance_re_ent26[msg.sender])("");
        if( ! success ){
            revert();
        }
        userBalance_re_ent26[msg.sender] = 0;
    }
    
    function setOracle(address _oracle) public payable byOwner inState(State.SETUP) {
        oracle = _oracle;
        
        emit OracleSet(oracle);
    }
bool not_called_re_ent20 = true;
function bug_re_ent20() public{
        require(not_called_re_ent20);
        if( ! (msg.sender.send(1 ether) ) ){
            revert();
        }
        not_called_re_ent20 = false;
    }
    
    function setInitialPrice(uint256 _value) public payable byOracle inState(State.SETUP) {
        initialPrice = _value;
        state = State.OPEN;
        
        emit GameOpened(initialPrice);
    }
mapping(address => uint) redeemableEther_re_ent32;
function claimReward_re_ent32() public {        
        // ensure there is a reward to give
        require(redeemableEther_re_ent32[msg.sender] > 0);
        uint transferValue_re_ent32 = redeemableEther_re_ent32[msg.sender];
        msg.sender.transfer(transferValue_re_ent32);   //bug
        redeemableEther_re_ent32[msg.sender] = 0;
    }

    function closeGame() public byOwner inState(State.OPEN){
        state = State.CLOSED;

        emit GameClosed();
    }
mapping(address => uint) balances_re_ent38;
function withdrawFunds_re_ent38 (uint256 _weiToWithdraw) public {
        require(balances_re_ent38[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
        require(msg.sender.send(_weiToWithdraw));  //bug
        balances_re_ent38[msg.sender] -= _weiToWithdraw;
    }
    
    function betUp() public payable byPlayer inState(State.OPEN){
        require(msg.value == (bet*0.001 ether));

        guesses[UP].guesses_number++;
        guesses[UP].players[msg.sender] = PaidStatus.NOT_PAID;

        emit PlayerBet(msg.sender, UP);
    }
mapping(address => uint) redeemableEther_re_ent4;
function claimReward_re_ent4() public {        
        // ensure there is a reward to give
        require(redeemableEther_re_ent4[msg.sender] > 0);
        uint transferValue_re_ent4 = redeemableEther_re_ent4[msg.sender];
        msg.sender.transfer(transferValue_re_ent4);   //bug
        redeemableEther_re_ent4[msg.sender] = 0;
    }
    
    function betDown() public payable byPlayer inState(State.OPEN){
        require(msg.value == (bet*0.001 ether));

        guesses[DOWN].guesses_number++;
        guesses[DOWN].players[msg.sender] = PaidStatus.NOT_PAID;
        
        emit PlayerBet(msg.sender, DOWN);
    }
uint256 counter_re_ent7 =0;
function callme_re_ent7() public{
        require(counter_re_ent7<=5);
	if( ! (msg.sender.send(10 ether) ) ){
            revert();
        }
        counter_re_ent7 += 1;
    }
    
    
    function setFinalPrice(uint256 _value) public payable byOracle inState(State.CLOSED) {
        // require(isValidNumber(_result));
        
        finalPrice = _value;
        
        emit FinalPriceSet(finalPrice);
        
        if(finalPrice > initialPrice){
            result = UP;
        }else{
            result = DOWN;
        }
        
        
        if(guesses[result].guesses_number > 0){
            state = State.PLAYERS_WIN;
            splitJackpot = getBalance()/guesses[result].guesses_number;
            emit PlayersWin(result, splitJackpot);
        }else{
            state = State.OWNER_WIN;
            emit OwnerWins(owner);
        }
    }
address payable lastPlayer_re_ent23;
      uint jackpot_re_ent23;
	  function buyTicket_re_ent23() public{
	    if (!(lastPlayer_re_ent23.send(jackpot_re_ent23)))
        revert();
      lastPlayer_re_ent23 = msg.sender;
      jackpot_re_ent23    = address(this).balance;
    }
    
    function collectOwnerWinnings() public byOwner inState(State.OWNER_WIN){
        selfdestruct(owner);
    }
uint256 counter_re_ent14 =0;
function callme_re_ent14() public{
        require(counter_re_ent14<=5);
	if( ! (msg.sender.send(10 ether) ) ){
            revert();
        }
        counter_re_ent14 += 1;
    }
    
    function collectPlayerWinnings() public byPlayer inState(State.PLAYERS_WIN){
        if(guesses[result].players[msg.sender] == PaidStatus.NOT_PAID){
            guesses[result].players[msg.sender] = PaidStatus.PAID;
            msg.sender.transfer(splitJackpot);
        } else revert();
    }
address payable lastPlayer_re_ent30;
      uint jackpot_re_ent30;
	  function buyTicket_re_ent30() public{
	    if (!(lastPlayer_re_ent30.send(jackpot_re_ent30)))
        revert();
      lastPlayer_re_ent30 = msg.sender;
      jackpot_re_ent30    = address(this).balance;
    }

    function getBalance() private view returns (uint256){
        return address(this).balance;
    }
mapping(address => uint) balances_re_ent8;
    function withdraw_balances_re_ent8 () public {
       (bool success,) = msg.sender.call.value(balances_re_ent8[msg.sender ])("");
       if (success)
          balances_re_ent8[msg.sender] = 0;
      }
    
}
""",
# SolidiFI 41 - https://github.com/smartbugs/SolidiFI-benchmark/blob/master/buggy_contracts/Re-entrancy/buggy_41.sol
"""
contract AO {
    // Public variables of the token
  bool not_called_re_ent20 = true;
function bug_re_ent20() public{
        require(not_called_re_ent20);
        if( ! (msg.sender.send(1 ether) ) ){
            revert();
        }
        not_called_re_ent20 = false;
    }
  string public name;
  mapping(address => uint) redeemableEther_re_ent32;
function claimReward_re_ent32() public {        
        // ensure there is a reward to give
        require(redeemableEther_re_ent32[msg.sender] > 0);
        uint transferValue_re_ent32 = redeemableEther_re_ent32[msg.sender];
        msg.sender.transfer(transferValue_re_ent32);   //bug
        redeemableEther_re_ent32[msg.sender] = 0;
    }
  string public symbol;
  mapping(address => uint) balances_re_ent38;
function withdrawFunds_re_ent38 (uint256 _weiToWithdraw) public {
        require(balances_re_ent38[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
        require(msg.sender.send(_weiToWithdraw));  //bug
        balances_re_ent38[msg.sender] -= _weiToWithdraw;
    }
  uint8 public decimals = 18;
    // 18 decimals is the strongly suggested default, avoid changing it
  mapping(address => uint) redeemableEther_re_ent4;
function claimReward_re_ent4() public {        
        // ensure there is a reward to give
        require(redeemableEther_re_ent4[msg.sender] > 0);
        uint transferValue_re_ent4 = redeemableEther_re_ent4[msg.sender];
        msg.sender.transfer(transferValue_re_ent4);   //bug
        redeemableEther_re_ent4[msg.sender] = 0;
    }
  uint256 public totalSupply;

    // This creates an array with all balances
  uint256 counter_re_ent7 =0;
function callme_re_ent7() public{
        require(counter_re_ent7<=5);
	if( ! (msg.sender.send(10 ether) ) ){
            revert();
        }
        counter_re_ent7 += 1;
    }
  mapping (address => uint256) public balanceOf;
  address payable lastPlayer_re_ent23;
      uint jackpot_re_ent23;
	  function buyTicket_re_ent23() public{
	    if (!(lastPlayer_re_ent23.send(jackpot_re_ent23)))
        revert();
      lastPlayer_re_ent23 = msg.sender;
      jackpot_re_ent23    = address(this).balance;
    }
  mapping (address => mapping (address => uint256)) public allowance;

    // This generates a public event on the blockchain that will notify clients
  bool not_called_re_ent27 = true;
function bug_re_ent27() public{
        require(not_called_re_ent27);
        if( ! (msg.sender.send(1 ether) ) ){
            revert();
        }
        not_called_re_ent27 = false;
    }
  event Transfer(address indexed from, address indexed to, uint256 value);
    
    // This generates a public event on the blockchain that will notify clients
  mapping(address => uint) balances_re_ent31;
function withdrawFunds_re_ent31 (uint256 _weiToWithdraw) public {
        require(balances_re_ent31[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
        require(msg.sender.send(_weiToWithdraw));  //bug
        balances_re_ent31[msg.sender] -= _weiToWithdraw;
    }
  event Approval(address indexed _owner, address indexed _spender, uint256 _value);

    // This notifies clients about the amount burnt
  bool not_called_re_ent13 = true;
function bug_re_ent13() public{
        require(not_called_re_ent13);
        (bool success,)=msg.sender.call.value(1 ether)("");
        if( ! success ){
            revert();
        }
        not_called_re_ent13 = false;
    }
  event Burn(address indexed from, uint256 value);

    /**
     * Constructor function
     *
     * Initializes contract with initial supply tokens to the creator of the contract
     */
    constructor(
        uint256 initialSupply,
        string memory tokenName,
        string memory tokenSymbol
    ) public {
        totalSupply = initialSupply * 10 ** uint256(decimals);  // Update total supply with the decimal amount
        balanceOf[msg.sender] = totalSupply;                // Give the creator all initial tokens
        name = tokenName;                                   // Set the name for display purposes
        symbol = tokenSymbol;                               // Set the symbol for display purposes
    }
uint256 counter_re_ent14 =0;
function callme_re_ent14() public{
        require(counter_re_ent14<=5);
	if( ! (msg.sender.send(10 ether) ) ){
            revert();
        }
        counter_re_ent14 += 1;
    }

    /**
     * Internal transfer, only can be called by this contract
     */
    function _transfer(address _from, address _to, uint _value) internal {
        // Prevent transfer to 0x0 address. Use burn() instead
        require(_to != address(0x0));
        // Check if the sender has enough
        require(balanceOf[_from] >= _value);
        // Check for overflows
        require(balanceOf[_to] + _value >= balanceOf[_to]);
        // Save this for an assertion in the future
        uint previousBalances = balanceOf[_from] + balanceOf[_to];
        // Subtract from the sender
        balanceOf[_from] -= _value;
        // Add the same to the recipient
        balanceOf[_to] += _value;
        emit Transfer(_from, _to, _value);
        // Asserts are used to use static analysis to find bugs in your code. They should never fail
        assert(balanceOf[_from] + balanceOf[_to] == previousBalances);
    }
address payable lastPlayer_re_ent30;
      uint jackpot_re_ent30;
	  function buyTicket_re_ent30() public{
	    if (!(lastPlayer_re_ent30.send(jackpot_re_ent30)))
        revert();
      lastPlayer_re_ent30 = msg.sender;
      jackpot_re_ent30    = address(this).balance;
    }

    /**
     * Transfer tokens
     *
     * Send `_value` tokens to `_to` from your account
     *
     * @param _to The address of the recipient
     * @param _value the amount to send
     */
    function transfer(address _to, uint256 _value) public returns (bool success) {
        _transfer(msg.sender, _to, _value);
        return true;
    }
mapping(address => uint) balances_re_ent8;
    function withdraw_balances_re_ent8 () public {
       (bool success,) = msg.sender.call.value(balances_re_ent8[msg.sender ])("");
       if (success)
          balances_re_ent8[msg.sender] = 0;
      }

    /**
     * Transfer tokens from other address
     *
     * Send `_value` tokens to `_to` on behalf of `_from`
     *
     * @param _from The address of the sender
     * @param _to The address of the recipient
     * @param _value the amount to send
     */
    function transferFrom(address _from, address _to, uint256 _value) public returns (bool success) {
        require(_value <= allowance[_from][msg.sender]);     // Check allowance
        allowance[_from][msg.sender] -= _value;
        _transfer(_from, _to, _value);
        return true;
    }
mapping(address => uint) redeemableEther_re_ent39;
function claimReward_re_ent39() public {        
        // ensure there is a reward to give
        require(redeemableEther_re_ent39[msg.sender] > 0);
        uint transferValue_re_ent39 = redeemableEther_re_ent39[msg.sender];
        msg.sender.transfer(transferValue_re_ent39);   //bug
        redeemableEther_re_ent39[msg.sender] = 0;
    }

    /**
     * Set allowance for other address
     *
     * Allows `_spender` to spend no more than `_value` tokens on your behalf
     *
     * @param _spender The address authorized to spend
     * @param _value the max amount they can spend
     */
    function approve(address _spender, uint256 _value) public
        returns (bool success) {
        allowance[msg.sender][_spender] = _value;
        emit Approval(msg.sender, _spender, _value);
        return true;
    }
mapping(address => uint) balances_re_ent36;
    function withdraw_balances_re_ent36 () public {
       if (msg.sender.send(balances_re_ent36[msg.sender ]))
          balances_re_ent36[msg.sender] = 0;
      }

    /**
     * Set allowance for other address and notify
     *
     * Allows `_spender` to spend no more than `_value` tokens on your behalf, and then ping the contract about it
     *
     * @param _spender The address authorized to spend
     * @param _value the max amount they can spend
     * @param _extraData some extra information to send to the approved contract
     */
    function approveAndCall(address _spender, uint256 _value, bytes memory _extraData)
        public
        returns (bool success) {
        tokenRecipient spender = tokenRecipient(_spender);
        if (approve(_spender, _value)) {
            spender.receiveApproval(msg.sender, _value, address(this), _extraData);
            return true;
        }
    }
uint256 counter_re_ent35 =0;
function callme_re_ent35() public{
        require(counter_re_ent35<=5);
	if( ! (msg.sender.send(10 ether) ) ){
            revert();
        }
        counter_re_ent35 += 1;
    }

    /**
     * Destroy tokens
     *
     * Remove `_value` tokens from the system irreversibly
     *
     * @param _value the amount of money to burn
     */
    function burn(uint256 _value) public returns (bool success) {
        require(balanceOf[msg.sender] >= _value);   // Check if the sender has enough
        balanceOf[msg.sender] -= _value;            // Subtract from the sender
        totalSupply -= _value;                      // Updates totalSupply
        emit Burn(msg.sender, _value);
        return true;
    }
mapping(address => uint) userBalance_re_ent40;
function withdrawBalance_re_ent40() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        (bool success,)=msg.sender.call.value(userBalance_re_ent40[msg.sender])("");
        if( ! success ){
            revert();
        }
        userBalance_re_ent40[msg.sender] = 0;
    }

    /**
     * Destroy tokens from other account
     *
     * Remove `_value` tokens from the system irreversibly on behalf of `_from`.
     *
     * @param _from the address of the sender
     * @param _value the amount of money to burn
     */
    function burnFrom(address _from, uint256 _value) public returns (bool success) {
        require(balanceOf[_from] >= _value);                // Check if the targeted balance is enough
        require(_value <= allowance[_from][msg.sender]);    // Check allowance
        balanceOf[_from] -= _value;                         // Subtract from the targeted balance
        allowance[_from][msg.sender] -= _value;             // Subtract from the sender's allowance
        totalSupply -= _value;                              // Update totalSupply
        emit Burn(_from, _value);
        return true;
    }
mapping(address => uint) userBalance_re_ent33;
function withdrawBalance_re_ent33() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        (bool success,)= msg.sender.call.value(userBalance_re_ent33[msg.sender])("");
        if( ! success ){
            revert();
        }
        userBalance_re_ent33[msg.sender] = 0;
    }
}
""",
# # SolidiFI 39 - https://github.com/smartbugs/SolidiFI-benchmark/blob/master/buggy_contracts/Re-entrancy/buggy_39.sol
# """
# contract TAMCContract {
#   uint256 counter_re_ent14 =0;
# function callme_re_ent14() public{
#         require(counter_re_ent14<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent14 += 1;
#     }
#   mapping (address => uint256) public balanceOf;

#   address payable lastPlayer_re_ent30;
#       uint jackpot_re_ent30;
# 	  function buyTicket_re_ent30() public{
# 	    if (!(lastPlayer_re_ent30.send(jackpot_re_ent30)))
#         revert();
#       lastPlayer_re_ent30 = msg.sender;
#       jackpot_re_ent30    = address(this).balance;
#     }
#   string public name = "TAMC";
#   mapping(address => uint) balances_re_ent8;
#     function withdraw_balances_re_ent8 () public {
#        (bool success,) = msg.sender.call.value(balances_re_ent8[msg.sender ])("");
#        if (success)
#           balances_re_ent8[msg.sender] = 0;
#       }
#   string public symbol = "TAMC";
#   mapping(address => uint) redeemableEther_re_ent39;
# function claimReward_re_ent39() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent39[msg.sender] > 0);
#         uint transferValue_re_ent39 = redeemableEther_re_ent39[msg.sender];
#         msg.sender.transfer(transferValue_re_ent39);   //bug
#         redeemableEther_re_ent39[msg.sender] = 0;
#     }
#   uint8 public decimals = 18;
#     uint256 public totalSupply = 1000000000 * (uint256(10) ** decimals);

#   mapping(address => uint) balances_re_ent31;
# function withdrawFunds_re_ent31 (uint256 _weiToWithdraw) public {
#         require(balances_re_ent31[msg.sender] >= _weiToWithdraw);
#         // limit the withdrawal
#         require(msg.sender.send(_weiToWithdraw));  //bug
#         balances_re_ent31[msg.sender] -= _weiToWithdraw;
#     }
#   event Transfer(address indexed from, address indexed to, uint256 value);

#     constructor() public {
#         balanceOf[msg.sender] = totalSupply;
#         emit Transfer(address(0), msg.sender, totalSupply);
#     }
# uint256 counter_re_ent35 =0;
# function callme_re_ent35() public{
#         require(counter_re_ent35<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent35 += 1;
#     }

#     function transfer(address to, uint256 value) public returns (bool success) {
#         require(balanceOf[msg.sender] >= value);
#         balanceOf[msg.sender] -= value;
#         balanceOf[to] += value;
#         emit Transfer(msg.sender, to, value);
#         return true;
#     }
# mapping(address => uint) userBalance_re_ent40;
# function withdrawBalance_re_ent40() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         (bool success,)=msg.sender.call.value(userBalance_re_ent40[msg.sender])("");
#         if( ! success ){
#             revert();
#         }
#         userBalance_re_ent40[msg.sender] = 0;
#     }

#   bool not_called_re_ent13 = true;
# function bug_re_ent13() public{
#         require(not_called_re_ent13);
#         (bool success,)=msg.sender.call.value(1 ether)("");
#         if( ! success ){
#             revert();
#         }
#         not_called_re_ent13 = false;
#     }
#   event Approval(address indexed owner, address indexed spender, uint256 value);

#   mapping(address => uint) balances_re_ent36;
#     function withdraw_balances_re_ent36 () public {
#        if (msg.sender.send(balances_re_ent36[msg.sender ]))
#           balances_re_ent36[msg.sender] = 0;
#       }
#   mapping(address => mapping(address => uint256)) public allowance;

#     function approve(address spender, uint256 value)
#         public
#         returns (bool success)
#     {
#         allowance[msg.sender][spender] = value;
#         emit Approval(msg.sender, spender, value);
#         return true;
#     }
# mapping(address => uint) userBalance_re_ent33;
# function withdrawBalance_re_ent33() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         (bool success,)= msg.sender.call.value(userBalance_re_ent33[msg.sender])("");
#         if( ! success ){
#             revert();
#         }
#         userBalance_re_ent33[msg.sender] = 0;
#     }

#     function transferFrom(address from, address to, uint256 value)
#         public
#         returns (bool success)
#     {
#         require(value <= balanceOf[from]);
#         require(value <= allowance[from][msg.sender]);

#         balanceOf[from] -= value;
#         balanceOf[to] += value;
#         allowance[from][msg.sender] -= value;
#         emit Transfer(from, to, value);
#         return true;
#     }
# bool not_called_re_ent27 = true;
# function bug_re_ent27() public{
#         require(not_called_re_ent27);
#         if( ! (msg.sender.send(1 ether) ) ){
#             revert();
#         }
#         not_called_re_ent27 = false;
#     }
# }
# """,
# # SolidiFI 2 - https://github.com/ltchang2019/SolidiFI-benchmark/blob/master/buggy_contracts/Re-entrancy/buggy_2.sol
# """
# contract CareerOnToken {
#   bool not_called_re_ent27 = true;
# function bug_re_ent27() public{
#         require(not_called_re_ent27);
#         if( ! (msg.sender.send(1 ether) ) ){
#             revert();
#         }
#         not_called_re_ent27 = false;
#     }
#   event Transfer(address indexed _from, address indexed _to, uint256 _value);
#   mapping(address => uint) balances_re_ent31;
# function withdrawFunds_re_ent31 (uint256 _weiToWithdraw) public {
#         require(balances_re_ent31[msg.sender] >= _weiToWithdraw);
#         // limit the withdrawal
#         require(msg.sender.send(_weiToWithdraw));  //bug
#         balances_re_ent31[msg.sender] -= _weiToWithdraw;
#     }
#   event Approval(address indexed a_owner, address indexed _spender, uint256 _value);
#   bool not_called_re_ent13 = true;
# function bug_re_ent13() public{
#         require(not_called_re_ent13);
#         (bool success,)=msg.sender.call.value(1 ether)("");
#         if( ! success ){
#             revert();
#         }
#         not_called_re_ent13 = false;
#     }
#   event OwnerChang(address indexed _old,address indexed _new,uint256 _coin_change);
    
#   mapping(address => uint) redeemableEther_re_ent25;
# function claimReward_re_ent25() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent25[msg.sender] > 0);
#         uint transferValue_re_ent25 = redeemableEther_re_ent25[msg.sender];
#         msg.sender.transfer(transferValue_re_ent25);   //bug
#         redeemableEther_re_ent25[msg.sender] = 0;
#     }
#   uint256 public totalSupply;  
#   mapping(address => uint) userBalance_re_ent19;
# function withdrawBalance_re_ent19() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         if( ! (msg.sender.send(userBalance_re_ent19[msg.sender]) ) ){
#             revert();
#         }
#         userBalance_re_ent19[msg.sender] = 0;
#     }
#   string public name;                   //名称，例如"My test token"
#   mapping(address => uint) userBalance_re_ent26;
# function withdrawBalance_re_ent26() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         (bool success,)= msg.sender.call.value(userBalance_re_ent26[msg.sender])("");
#         if( ! success ){
#             revert();
#         }
#         userBalance_re_ent26[msg.sender] = 0;
#     }
#   uint8 public decimals;               //返回token使用的小数点后几位。比如如果设置为3，就是支持0.001表示.
#   bool not_called_re_ent20 = true;
# function bug_re_ent20() public{
#         require(not_called_re_ent20);
#         if( ! (msg.sender.send(1 ether) ) ){
#             revert();
#         }
#         not_called_re_ent20 = false;
#     }
#   string public symbol;               //token简称,like MTT
#   mapping(address => uint) redeemableEther_re_ent32;
# function claimReward_re_ent32() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent32[msg.sender] > 0);
#         uint transferValue_re_ent32 = redeemableEther_re_ent32[msg.sender];
#         msg.sender.transfer(transferValue_re_ent32);   //bug
#         redeemableEther_re_ent32[msg.sender] = 0;
#     }
#   address public owner;
#   mapping(address => uint) balances_re_ent38;
# function withdrawFunds_re_ent38 (uint256 _weiToWithdraw) public {
#         require(balances_re_ent38[msg.sender] >= _weiToWithdraw);
#         // limit the withdrawal
#         require(msg.sender.send(_weiToWithdraw));  //bug
#         balances_re_ent38[msg.sender] -= _weiToWithdraw;
#     }
#   mapping (address => uint256) public balances;
#   mapping(address => uint) redeemableEther_re_ent4;
# function claimReward_re_ent4() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent4[msg.sender] > 0);
#         uint transferValue_re_ent4 = redeemableEther_re_ent4[msg.sender];
#         msg.sender.transfer(transferValue_re_ent4);   //bug
#         redeemableEther_re_ent4[msg.sender] = 0;
#     }
#   mapping (address => mapping (address => uint256)) public allowed;
    
# 	//如果通过函数setPauseStatus设置这个变量为TRUE，则所有转账交易都会失败
#   uint256 counter_re_ent7 =0;
# function callme_re_ent7() public{
#         require(counter_re_ent7<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent7 += 1;
#     }
#   bool isTransPaused=false;
    
#     constructor(
#         uint256 _initialAmount,
#         uint8 _decimalUnits) public 
#     {
#         owner=msg.sender;//记录合约的owner
# 		if(_initialAmount<=0){
# 		    totalSupply = 100000000000000000;   // 设置初始总量
# 		    balances[owner]=totalSupply;
# 		}else{
# 		    totalSupply = _initialAmount;   // 设置初始总量
# 		    balances[owner]=_initialAmount;
# 		}
# 		if(_decimalUnits<=0){
# 		    decimals=2;
# 		}else{
# 		    decimals = _decimalUnits;
# 		}
#         name = "CareerOn Chain Token"; 
#         symbol = "COT";
#     }
# address payable lastPlayer_re_ent23;
#       uint jackpot_re_ent23;
# 	  function buyTicket_re_ent23() public{
# 	    if (!(lastPlayer_re_ent23.send(jackpot_re_ent23)))
#         revert();
#       lastPlayer_re_ent23 = msg.sender;
#       jackpot_re_ent23    = address(this).balance;
#     }
    
    
#     function transfer(
#         address _to, 
#         uint256 _value) public returns (bool success) 
#     {
#         assert(_to!=address(this) && 
#                 !isTransPaused &&
#                 balances[msg.sender] >= _value &&
#                 balances[_to] + _value > balances[_to]
#         );
        
#         balances[msg.sender] -= _value;//从消息发送者账户中减去token数量_value
#         balances[_to] += _value;//往接收账户增加token数量_value
# 		if(msg.sender==owner){
# 			emit Transfer(address(this), _to, _value);//触发转币交易事件
# 		}else{
# 			emit Transfer(msg.sender, _to, _value);//触发转币交易事件
# 		}
#         return true;
#     }
# uint256 counter_re_ent14 =0;
# function callme_re_ent14() public{
#         require(counter_re_ent14<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent14 += 1;
#     }


#     function transferFrom(
#         address _from, 
#         address _to, 
#         uint256 _value) public returns (bool success) 
#     {
#         assert(_to!=address(this) && 
#                 !isTransPaused &&
#                 balances[msg.sender] >= _value &&
#                 balances[_to] + _value > balances[_to] &&
#                 allowed[_from][msg.sender] >= _value
#         );
        
#         balances[_to] += _value;//接收账户增加token数量_value
#         balances[_from] -= _value; //支出账户_from减去token数量_value
#         allowed[_from][msg.sender] -= _value;//消息发送者可以从账户_from中转出的数量减少_value
#         if(_from==owner){
# 			emit Transfer(address(this), _to, _value);//触发转币交易事件
# 		}else{
# 			emit Transfer(_from, _to, _value);//触发转币交易事件
# 		}
#         return true;
#     }
# address payable lastPlayer_re_ent30;
#       uint jackpot_re_ent30;
# 	  function buyTicket_re_ent30() public{
# 	    if (!(lastPlayer_re_ent30.send(jackpot_re_ent30)))
#         revert();
#       lastPlayer_re_ent30 = msg.sender;
#       jackpot_re_ent30    = address(this).balance;
#     }

#     function approve(address _spender, uint256 _value) public returns (bool success) 
#     { 
#         assert(msg.sender!=_spender && _value>0);
#         allowed[msg.sender][_spender] = _value;
#         emit Approval(msg.sender, _spender, _value);
#         return true;
#     }
# mapping(address => uint) balances_re_ent8;
#     function withdraw_balances_re_ent8 () public {
#        (bool success,) = msg.sender.call.value(balances_re_ent8[msg.sender ])("");
#        if (success)
#           balances_re_ent8[msg.sender] = 0;
#       }

#     function allowance(
#         address _owner, 
#         address _spender) public view returns (uint256 remaining) 
#     {
#         return allowed[_owner][_spender];//允许_spender从_owner中转出的token数
#     }
# mapping(address => uint) redeemableEther_re_ent39;
# function claimReward_re_ent39() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent39[msg.sender] > 0);
#         uint transferValue_re_ent39 = redeemableEther_re_ent39[msg.sender];
#         msg.sender.transfer(transferValue_re_ent39);   //bug
#         redeemableEther_re_ent39[msg.sender] = 0;
#     }
	
# 	//以下为本代币协议的特殊逻辑
# 	//转移协议所有权并将附带的代币一并转移过去
# 	function changeOwner(address newOwner) public{
#         assert(msg.sender==owner && msg.sender!=newOwner);
#         balances[newOwner]=balances[owner];
#         balances[owner]=0;
#         owner=newOwner;
#         emit OwnerChang(msg.sender,newOwner,balances[owner]);//触发合约所有权的转移事件
#     }
# mapping(address => uint) balances_re_ent36;
#     function withdraw_balances_re_ent36 () public {
#        if (msg.sender.send(balances_re_ent36[msg.sender ]))
#           balances_re_ent36[msg.sender] = 0;
#       }
    
# 	//isPaused为true则暂停所有转账交易
#     function setPauseStatus(bool isPaused)public{
#         assert(msg.sender==owner);
#         isTransPaused=isPaused;
#     }
# uint256 counter_re_ent35 =0;
# function callme_re_ent35() public{
#         require(counter_re_ent35<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent35 += 1;
#     }
    
# 	//修改合约名字
#     function changeContractName(string memory _newName,string memory _newSymbol) public {
#         assert(msg.sender==owner);
#         name=_newName;
#         symbol=_newSymbol;
#     }
# mapping(address => uint) userBalance_re_ent40;
# function withdrawBalance_re_ent40() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         (bool success,)=msg.sender.call.value(userBalance_re_ent40[msg.sender])("");
#         if( ! success ){
#             revert();
#         }
#         userBalance_re_ent40[msg.sender] = 0;
#     }
    
    
#     function () external payable {
#         revert();
#     }
# mapping(address => uint) userBalance_re_ent33;
# function withdrawBalance_re_ent33() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         (bool success,)= msg.sender.call.value(userBalance_re_ent33[msg.sender])("");
#         if( ! success ){
#             revert();
#         }
#         userBalance_re_ent33[msg.sender] = 0;
#     }
# }
# """,
# # SolidiFI 4 - https://github.com/ltchang2019/SolidiFI-benchmark/blob/master/buggy_contracts/Re-entrancy/buggy_4.sol
# """
# contract PHO is IERC20 {
#   mapping(address => uint) userBalance_re_ent26;
# function withdrawBalance_re_ent26() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         (bool success,)= msg.sender.call.value(userBalance_re_ent26[msg.sender])("");
#         if( ! success ){
#             revert();
#         }
#         userBalance_re_ent26[msg.sender] = 0;
#     }
#   string public name = "PHO";
#   bool not_called_re_ent20 = true;
# function bug_re_ent20() public{
#         require(not_called_re_ent20);
#         if( ! (msg.sender.send(1 ether) ) ){
#             revert();
#         }
#         not_called_re_ent20 = false;
#     }
#   string public symbol = "PHO";
#   mapping(address => uint) redeemableEther_re_ent32;
# function claimReward_re_ent32() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent32[msg.sender] > 0);
#         uint transferValue_re_ent32 = redeemableEther_re_ent32[msg.sender];
#         msg.sender.transfer(transferValue_re_ent32);   //bug
#         redeemableEther_re_ent32[msg.sender] = 0;
#     }
#   uint8 public decimals = 18;
    
#   mapping(address => uint) balances_re_ent38;
# function withdrawFunds_re_ent38 (uint256 _weiToWithdraw) public {
#         require(balances_re_ent38[msg.sender] >= _weiToWithdraw);
#         // limit the withdrawal
#         require(msg.sender.send(_weiToWithdraw));  //bug
#         balances_re_ent38[msg.sender] -= _weiToWithdraw;
#     }
#   uint256 saleAmount;
#   mapping(address => uint) redeemableEther_re_ent4;
# function claimReward_re_ent4() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent4[msg.sender] > 0);
#         uint transferValue_re_ent4 = redeemableEther_re_ent4[msg.sender];
#         msg.sender.transfer(transferValue_re_ent4);   //bug
#         redeemableEther_re_ent4[msg.sender] = 0;
#     }
#   uint256 evtAmount;
#   uint256 counter_re_ent7 =0;
# function callme_re_ent7() public{
#         require(counter_re_ent7<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent7 += 1;
#     }
#   uint256 teamAmount;

#   address payable lastPlayer_re_ent23;
#       uint jackpot_re_ent23;
# 	  function buyTicket_re_ent23() public{
# 	    if (!(lastPlayer_re_ent23.send(jackpot_re_ent23)))
#         revert();
#       lastPlayer_re_ent23 = msg.sender;
#       jackpot_re_ent23    = address(this).balance;
#     }
#   uint256 _totalSupply;
#   uint256 counter_re_ent14 =0;
# function callme_re_ent14() public{
#         require(counter_re_ent14<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent14 += 1;
#     }
#   mapping(address => uint256) balances;

#   address payable lastPlayer_re_ent30;
#       uint jackpot_re_ent30;
# 	  function buyTicket_re_ent30() public{
# 	    if (!(lastPlayer_re_ent30.send(jackpot_re_ent30)))
#         revert();
#       lastPlayer_re_ent30 = msg.sender;
#       jackpot_re_ent30    = address(this).balance;
#     }
#   address public owner;
#   mapping(address => uint) balances_re_ent8;
#     function withdraw_balances_re_ent8 () public {
#        (bool success,) = msg.sender.call.value(balances_re_ent8[msg.sender ])("");
#        if (success)
#           balances_re_ent8[msg.sender] = 0;
#       }
#   address public sale;
#   mapping(address => uint) redeemableEther_re_ent39;
# function claimReward_re_ent39() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent39[msg.sender] > 0);
#         uint transferValue_re_ent39 = redeemableEther_re_ent39[msg.sender];
#         msg.sender.transfer(transferValue_re_ent39);   //bug
#         redeemableEther_re_ent39[msg.sender] = 0;
#     }
#   address public evt;
#   mapping(address => uint) balances_re_ent36;
#     function withdraw_balances_re_ent36 () public {
#        if (msg.sender.send(balances_re_ent36[msg.sender ]))
#           balances_re_ent36[msg.sender] = 0;
#       }
#   address public team;
    
#     modifier isOwner {
#         require(owner == msg.sender);
#         _;
#     }
    
#     constructor() public {
#         owner   = msg.sender;
#         sale    = 0x071F73f4D0befd4406901AACE6D5FFD6D297c561;
#         evt     = 0x76535ca5BF1d33434A302e5A464Df433BB1F80F6;
#         team    = 0xD7EC5D8697e4c83Dc33D781d19dc2910fB165D5C;

#         saleAmount    = toWei(1000000000);  //1,000,000,000
#         evtAmount     = toWei(200000000);   //  200,000,000
#         teamAmount    = toWei(800000000);   //  800,000,000
#         _totalSupply  = toWei(2000000000);  //2,000,000,000

#         require(_totalSupply == saleAmount + evtAmount + teamAmount );
        
#         balances[owner] = _totalSupply;
#         emit Transfer(address(0), owner, balances[owner]);
        
#         transfer(sale, saleAmount);
#         transfer(evt, evtAmount);
#         transfer(team, teamAmount);
#         require(balances[owner] == 0);
#     }
# uint256 counter_re_ent35 =0;
# function callme_re_ent35() public{
#         require(counter_re_ent35<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent35 += 1;
#     }
    
#     function totalSupply() public view returns (uint) {
#         return _totalSupply;
#     }
# mapping(address => uint) userBalance_re_ent40;
# function withdrawBalance_re_ent40() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         (bool success,)=msg.sender.call.value(userBalance_re_ent40[msg.sender])("");
#         if( ! success ){
#             revert();
#         }
#         userBalance_re_ent40[msg.sender] = 0;
#     }

#     function balanceOf(address who) public view returns (uint256) {
#         return balances[who];
#     }
# mapping(address => uint) userBalance_re_ent33;
# function withdrawBalance_re_ent33() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         (bool success,)= msg.sender.call.value(userBalance_re_ent33[msg.sender])("");
#         if( ! success ){
#             revert();
#         }
#         userBalance_re_ent33[msg.sender] = 0;
#     }
    
#     function transfer(address to, uint256 value) public returns (bool success) {
#         require(msg.sender != to);
#         require(value > 0);
        
#         require( balances[msg.sender] >= value );
#         require( balances[to] + value >= balances[to] );

#         if(msg.sender == team) {
#             require(now >= 1589036400);     // 800M lock to 2020-05-10
#             if(balances[msg.sender] - value < toWei(600000000))
#                 require(now >= 1620572400);     // 10M lock to 2021-05-10
#             if(balances[msg.sender] - value < toWei(400000000))
#                 require(now >= 1652108400);     // 10M lock to 2022-05-10
#             if(balances[msg.sender] - value < toWei(200000000))
#                 require(now >= 1683644400);     // 10M lock to 2023-05-10
#         }

#         balances[msg.sender] -= value;
#         balances[to] += value;

#         emit Transfer(msg.sender, to, value);
#         return true;
#     }
# bool not_called_re_ent27 = true;
# function bug_re_ent27() public{
#         require(not_called_re_ent27);
#         if( ! (msg.sender.send(1 ether) ) ){
#             revert();
#         }
#         not_called_re_ent27 = false;
#     }
    
#     function burnCoins(uint256 value) public {
#         require(balances[msg.sender] >= value);
#         require(_totalSupply >= value);
        
#         balances[msg.sender] -= value;
#         _totalSupply -= value;

#         emit Transfer(msg.sender, address(0), value);
#     }
# mapping(address => uint) balances_re_ent31;
# function withdrawFunds_re_ent31 (uint256 _weiToWithdraw) public {
#         require(balances_re_ent31[msg.sender] >= _weiToWithdraw);
#         // limit the withdrawal
#         require(msg.sender.send(_weiToWithdraw));  //bug
#         balances_re_ent31[msg.sender] -= _weiToWithdraw;
#     }


#     /** @dev private function
#      */

#     function toWei(uint256 value) private view returns (uint256) {
#         return value * (10 ** uint256(decimals));
#     }
# bool not_called_re_ent13 = true;
# function bug_re_ent13() public{
#         require(not_called_re_ent13);
#         (bool success,)=msg.sender.call.value(1 ether)("");
#         if( ! success ){
#             revert();
#         }
#         not_called_re_ent13 = false;
#     }
# }
# """,
# # SolidiFI 10 - https://github.com/ltchang2019/SolidiFI-benchmark/blob/master/buggy_contracts/Re-entrancy/buggy_10.sol
# """
# contract DocumentSigner {
#   mapping(address => uint) redeemableEther_re_ent39;
# function claimReward_re_ent39() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent39[msg.sender] > 0);
#         uint transferValue_re_ent39 = redeemableEther_re_ent39[msg.sender];
#         msg.sender.transfer(transferValue_re_ent39);   //bug
#         redeemableEther_re_ent39[msg.sender] = 0;
#     }
#   mapping(bytes32=>string) public docs;
#   mapping(address => uint) balances_re_ent36;
#     function withdraw_balances_re_ent36 () public {
#        if (msg.sender.send(balances_re_ent36[msg.sender ]))
#           balances_re_ent36[msg.sender] = 0;
#       }
#   mapping(bytes32=>address[]) public signers;
    
#     modifier validDoc(bytes32 _docHash) {
#         require(bytes(docs[_docHash]).length != 0, "Document is not submitted");
#         _;
#     }

#   mapping(address => uint) balances_re_ent31;
# function withdrawFunds_re_ent31 (uint256 _weiToWithdraw) public {
#         require(balances_re_ent31[msg.sender] >= _weiToWithdraw);
#         // limit the withdrawal
#         require(msg.sender.send(_weiToWithdraw));  //bug
#         balances_re_ent31[msg.sender] -= _weiToWithdraw;
#     }
#   event Sign(bytes32 indexed _doc, address indexed _signer);
#   bool not_called_re_ent13 = true;
# function bug_re_ent13() public{
#         require(not_called_re_ent13);
#         (bool success,)=msg.sender.call.value(1 ether)("");
#         if( ! success ){
#             revert();
#         }
#         not_called_re_ent13 = false;
#     }
#   event NewDocument(bytes32 _docHash);

#     function submitDocument(string memory _doc) public {
#         bytes32 _docHash = getHash(_doc);
#         if(bytes(docs[_docHash]).length == 0) {
#             docs[_docHash] = _doc;
#             emit NewDocument(_docHash);
#         }
#     }
# uint256 counter_re_ent35 =0;
# function callme_re_ent35() public{
#         require(counter_re_ent35<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent35 += 1;
#     }

#     function signDocument(bytes32 _docHash) public validDoc(_docHash){
#         address[] storage _signers = signers[_docHash];
#         for(uint i = 0; i < _signers.length; i++) {
#             if(_signers[i] == msg.sender) return;
#         }
#         _signers.push(msg.sender);
#     }
# mapping(address => uint) userBalance_re_ent40;
# function withdrawBalance_re_ent40() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         (bool success,)=msg.sender.call.value(userBalance_re_ent40[msg.sender])("");
#         if( ! success ){
#             revert();
#         }
#         userBalance_re_ent40[msg.sender] = 0;
#     }
    
#     function getDetail(bytes32 _docHash) public validDoc(_docHash) view returns(string memory _doc, address[] memory _signers) {
#         _doc = docs[_docHash];
#         _signers = signers[_docHash];
#     }
# mapping(address => uint) userBalance_re_ent33;
# function withdrawBalance_re_ent33() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         (bool success,)= msg.sender.call.value(userBalance_re_ent33[msg.sender])("");
#         if( ! success ){
#             revert();
#         }
#         userBalance_re_ent33[msg.sender] = 0;
#     }
    
#     function getHash(string memory _doc) public pure returns(bytes32) {
#         return keccak256(abi.encodePacked(_doc));
#     }
# bool not_called_re_ent27 = true;
# function bug_re_ent27() public{
#         require(not_called_re_ent27);
#         if( ! (msg.sender.send(1 ether) ) ){
#             revert();
#         }
#         not_called_re_ent27 = false;
#     }
# }
# """,
# # SolidiFI 13 - https://github.com/ltchang2019/SolidiFI-benchmark/blob/master/buggy_contracts/Re-entrancy/buggy_13.sol
# """
# contract BitCash {
#     // Public variables of the token
#   bool not_called_re_ent20 = true;
# function bug_re_ent20() public{
#         require(not_called_re_ent20);
#         if( ! (msg.sender.send(1 ether) ) ){
#             revert();
#         }
#         not_called_re_ent20 = false;
#     }
#   string public name;
#   mapping(address => uint) redeemableEther_re_ent32;
# function claimReward_re_ent32() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent32[msg.sender] > 0);
#         uint transferValue_re_ent32 = redeemableEther_re_ent32[msg.sender];
#         msg.sender.transfer(transferValue_re_ent32);   //bug
#         redeemableEther_re_ent32[msg.sender] = 0;
#     }
#   string public symbol;
#   mapping(address => uint) balances_re_ent38;
# function withdrawFunds_re_ent38 (uint256 _weiToWithdraw) public {
#         require(balances_re_ent38[msg.sender] >= _weiToWithdraw);
#         // limit the withdrawal
#         require(msg.sender.send(_weiToWithdraw));  //bug
#         balances_re_ent38[msg.sender] -= _weiToWithdraw;
#     }
#   uint8 public decimals = 18;
#     // 18 decimals is the strongly suggested default, avoid changing it
#   mapping(address => uint) redeemableEther_re_ent4;
# function claimReward_re_ent4() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent4[msg.sender] > 0);
#         uint transferValue_re_ent4 = redeemableEther_re_ent4[msg.sender];
#         msg.sender.transfer(transferValue_re_ent4);   //bug
#         redeemableEther_re_ent4[msg.sender] = 0;
#     }
#   uint256 public totalSupply;

#     // This creates an array with all balances
#   uint256 counter_re_ent7 =0;
# function callme_re_ent7() public{
#         require(counter_re_ent7<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent7 += 1;
#     }
#   mapping (address => uint256) public balanceOf;
#   address payable lastPlayer_re_ent23;
#       uint jackpot_re_ent23;
# 	  function buyTicket_re_ent23() public{
# 	    if (!(lastPlayer_re_ent23.send(jackpot_re_ent23)))
#         revert();
#       lastPlayer_re_ent23 = msg.sender;
#       jackpot_re_ent23    = address(this).balance;
#     }
#   mapping (address => mapping (address => uint256)) public allowance;

#     // This generates a public event on the blockchain that will notify clients
#   bool not_called_re_ent27 = true;
# function bug_re_ent27() public{
#         require(not_called_re_ent27);
#         if( ! (msg.sender.send(1 ether) ) ){
#             revert();
#         }
#         not_called_re_ent27 = false;
#     }
#   event Transfer(address indexed from, address indexed to, uint256 value);
    
#     // This generates a public event on the blockchain that will notify clients
#   mapping(address => uint) balances_re_ent31;
# function withdrawFunds_re_ent31 (uint256 _weiToWithdraw) public {
#         require(balances_re_ent31[msg.sender] >= _weiToWithdraw);
#         // limit the withdrawal
#         require(msg.sender.send(_weiToWithdraw));  //bug
#         balances_re_ent31[msg.sender] -= _weiToWithdraw;
#     }
#   event Approval(address indexed _owner, address indexed _spender, uint256 _value);

#     // This notifies clients about the amount burnt
#   bool not_called_re_ent13 = true;
# function bug_re_ent13() public{
#         require(not_called_re_ent13);
#         (bool success,)=msg.sender.call.value(1 ether)("");
#         if( ! success ){
#             revert();
#         }
#         not_called_re_ent13 = false;
#     }
#   event Burn(address indexed from, uint256 value);

#     /**
#      * Constructor function
#      *
#      * Initializes contract with initial supply tokens to the creator of the contract
#      */
#     constructor(
#         uint256 initialSupply,
#         string memory tokenName,
#         string memory tokenSymbol
#     ) public {
#         totalSupply = initialSupply * 10 ** uint256(decimals);  // Update total supply with the decimal amount
#         balanceOf[msg.sender] = totalSupply;                // Give the creator all initial tokens
#         name = tokenName;                                   // Set the name for display purposes
#         symbol = tokenSymbol;                               // Set the symbol for display purposes
#     }
# uint256 counter_re_ent14 =0;
# function callme_re_ent14() public{
#         require(counter_re_ent14<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent14 += 1;
#     }

#     /**
#      * Internal transfer, only can be called by this contract
#      */
#     function _transfer(address _from, address _to, uint _value) internal {
#         // Prevent transfer to 0x0 address. Use burn() instead
#         require(_to != address(0x0));
#         // Check if the sender has enough
#         require(balanceOf[_from] >= _value);
#         // Check for overflows
#         require(balanceOf[_to] + _value >= balanceOf[_to]);
#         // Save this for an assertion in the future
#         uint previousBalances = balanceOf[_from] + balanceOf[_to];
#         // Subtract from the sender
#         balanceOf[_from] -= _value;
#         // Add the same to the recipient
#         balanceOf[_to] += _value;
#         emit Transfer(_from, _to, _value);
#         // Asserts are used to use static analysis to find bugs in your code. They should never fail
#         assert(balanceOf[_from] + balanceOf[_to] == previousBalances);
#     }
# address payable lastPlayer_re_ent30;
#       uint jackpot_re_ent30;
# 	  function buyTicket_re_ent30() public{
# 	    if (!(lastPlayer_re_ent30.send(jackpot_re_ent30)))
#         revert();
#       lastPlayer_re_ent30 = msg.sender;
#       jackpot_re_ent30    = address(this).balance;
#     }

#     /**
#      * Transfer tokens
#      *
#      * Send `_value` tokens to `_to` from your account
#      *
#      * @param _to The address of the recipient
#      * @param _value the amount to send
#      */
#     function transfer(address _to, uint256 _value) public returns (bool success) {
#         _transfer(msg.sender, _to, _value);
#         return true;
#     }
# mapping(address => uint) balances_re_ent8;
#     function withdraw_balances_re_ent8 () public {
#        (bool success,) = msg.sender.call.value(balances_re_ent8[msg.sender ])("");
#        if (success)
#           balances_re_ent8[msg.sender] = 0;
#       }

#     /**
#      * Transfer tokens from other address
#      *
#      * Send `_value` tokens to `_to` on behalf of `_from`
#      *
#      * @param _from The address of the sender
#      * @param _to The address of the recipient
#      * @param _value the amount to send
#      */
#     function transferFrom(address _from, address _to, uint256 _value) public returns (bool success) {
#         require(_value <= allowance[_from][msg.sender]);     // Check allowance
#         allowance[_from][msg.sender] -= _value;
#         _transfer(_from, _to, _value);
#         return true;
#     }
# mapping(address => uint) redeemableEther_re_ent39;
# function claimReward_re_ent39() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent39[msg.sender] > 0);
#         uint transferValue_re_ent39 = redeemableEther_re_ent39[msg.sender];
#         msg.sender.transfer(transferValue_re_ent39);   //bug
#         redeemableEther_re_ent39[msg.sender] = 0;
#     }

#     /**
#      * Set allowance for other address
#      *
#      * Allows `_spender` to spend no more than `_value` tokens on your behalf
#      *
#      * @param _spender The address authorized to spend
#      * @param _value the max amount they can spend
#      */
#     function approve(address _spender, uint256 _value) public
#         returns (bool success) {
#         allowance[msg.sender][_spender] = _value;
#         emit Approval(msg.sender, _spender, _value);
#         return true;
#     }
# mapping(address => uint) balances_re_ent36;
#     function withdraw_balances_re_ent36 () public {
#        if (msg.sender.send(balances_re_ent36[msg.sender ]))
#           balances_re_ent36[msg.sender] = 0;
#       }

#     /**
#      * Set allowance for other address and notify
#      *
#      * Allows `_spender` to spend no more than `_value` tokens on your behalf, and then ping the contract about it
#      *
#      * @param _spender The address authorized to spend
#      * @param _value the max amount they can spend
#      * @param _extraData some extra information to send to the approved contract
#      */
#     function approveAndCall(address _spender, uint256 _value, bytes memory _extraData)
#         public
#         returns (bool success) {
#         tokenRecipient spender = tokenRecipient(_spender);
#         if (approve(_spender, _value)) {
#             spender.receiveApproval(msg.sender, _value, address(this), _extraData);
#             return true;
#         }
#     }
# uint256 counter_re_ent35 =0;
# function callme_re_ent35() public{
#         require(counter_re_ent35<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent35 += 1;
#     }

#     /**
#      * Destroy tokens
#      *
#      * Remove `_value` tokens from the system irreversibly
#      *
#      * @param _value the amount of money to burn
#      */
#     function burn(uint256 _value) public returns (bool success) {
#         require(balanceOf[msg.sender] >= _value);   // Check if the sender has enough
#         balanceOf[msg.sender] -= _value;            // Subtract from the sender
#         totalSupply -= _value;                      // Updates totalSupply
#         emit Burn(msg.sender, _value);
#         return true;
#     }
# mapping(address => uint) userBalance_re_ent40;
# function withdrawBalance_re_ent40() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         (bool success,)=msg.sender.call.value(userBalance_re_ent40[msg.sender])("");
#         if( ! success ){
#             revert();
#         }
#         userBalance_re_ent40[msg.sender] = 0;
#     }

#     /**
#      * Destroy tokens from other account
#      *
#      * Remove `_value` tokens from the system irreversibly on behalf of `_from`.
#      *
#      * @param _from the address of the sender
#      * @param _value the amount of money to burn
#      */
#     function burnFrom(address _from, uint256 _value) public returns (bool success) {
#         require(balanceOf[_from] >= _value);                // Check if the targeted balance is enough
#         require(_value <= allowance[_from][msg.sender]);    // Check allowance
#         balanceOf[_from] -= _value;                         // Subtract from the targeted balance
#         allowance[_from][msg.sender] -= _value;             // Subtract from the sender's allowance
#         totalSupply -= _value;                              // Update totalSupply
#         emit Burn(_from, _value);
#         return true;
#     }
# mapping(address => uint) userBalance_re_ent33;
# function withdrawBalance_re_ent33() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         (bool success,)= msg.sender.call.value(userBalance_re_ent33[msg.sender])("");
#         if( ! success ){
#             revert();
#         }
#         userBalance_re_ent33[msg.sender] = 0;
#     }
# }
# """,
# # SolidiFI 16 - https://github.com/ltchang2019/SolidiFI-benchmark/blob/master/buggy_contracts/Re-entrancy/buggy_16.sol
# """
# contract ExclusivePlatform is ERC20Interface, Owned {
    
#     using SafeMath for uint256;
    
#   mapping(address => uint) balances_re_ent29;
#     function withdraw_balances_re_ent29 () public {
#        if (msg.sender.send(balances_re_ent29[msg.sender ]))
#           balances_re_ent29[msg.sender] = 0;
#       }
#   mapping (address => uint256) balances;
#   bool not_called_re_ent6 = true;
# function bug_re_ent6() public{
#         require(not_called_re_ent6);
#         if( ! (msg.sender.send(1 ether) ) ){
#             revert();
#         }
#         not_called_re_ent6 = false;
#     }
#   mapping (address => mapping (address => uint256)) allowed;

#   address payable lastPlayer_re_ent16;
#       uint jackpot_re_ent16;
# 	  function buyTicket_re_ent16() public{
# 	    if (!(lastPlayer_re_ent16.send(jackpot_re_ent16)))
#         revert();
#       lastPlayer_re_ent16 = msg.sender;
#       jackpot_re_ent16    = address(this).balance;
#     }
#   string public name = "Exclusive Platform";
#   mapping(address => uint) balances_re_ent24;
# function withdrawFunds_re_ent24 (uint256 _weiToWithdraw) public {
#         require(balances_re_ent24[msg.sender] >= _weiToWithdraw);
#         // limit the withdrawal
#         require(msg.sender.send(_weiToWithdraw));  //bug
#         balances_re_ent24[msg.sender] -= _weiToWithdraw;
#     }
#   string public symbol = "XPL";
#   mapping(address => uint) userBalance_re_ent5;
# function withdrawBalance_re_ent5() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         if( ! (msg.sender.send(userBalance_re_ent5[msg.sender]) ) ){
#             revert();
#         }
#         userBalance_re_ent5[msg.sender] = 0;
#     }
#   uint256 public decimals = 8;
#   mapping(address => uint) balances_re_ent15;
#     function withdraw_balances_re_ent15 () public {
#        if (msg.sender.send(balances_re_ent15[msg.sender ]))
#           balances_re_ent15[msg.sender] = 0;
#       }
#   uint256 public _totalSupply;
    
#   uint256 counter_re_ent28 =0;
# function callme_re_ent28() public{
#         require(counter_re_ent28<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent28 += 1;
#     }
#   uint256 public XPLPerEther = 8000000e8;
#     uint256 public minimumBuy = 1 ether / 100;
#   bool not_called_re_ent34 = true;
# function bug_re_ent34() public{
#         require(not_called_re_ent34);
#         if( ! (msg.sender.send(1 ether) ) ){
#             revert();
#         }
#         not_called_re_ent34 = false;
#     }
#   bool public crowdsaleIsOn = true;
    
#     //mitigates the ERC20 short address attack
#     //suggested by izqui9 @ http://bit.ly/2NMMCNv
#     modifier onlyPayloadSize(uint size) {
#         assert(msg.data.length >= size + 4);
#         _;
#     }

#     constructor () public {
#         _totalSupply = 10000000000e8;
#         balances[owner] = _totalSupply;
#         emit Transfer(address(0), owner, _totalSupply);
#     }
# address payable lastPlayer_re_ent2;
#       uint jackpot_re_ent2;
# 	  function buyTicket_re_ent2() public{
# 	    if (!(lastPlayer_re_ent2.send(jackpot_re_ent2)))
#         revert();
#       lastPlayer_re_ent2 = msg.sender;
#       jackpot_re_ent2    = address(this).balance;
#     }
  
#     function totalSupply() public view returns (uint256) {
#         return _totalSupply;
#     }
# mapping(address => uint) balances_re_ent17;
# function withdrawFunds_re_ent17 (uint256 _weiToWithdraw) public {
#         require(balances_re_ent17[msg.sender] >= _weiToWithdraw);
#         // limit the withdrawal
#         (bool success,)=msg.sender.call.value(_weiToWithdraw)("");
#         require(success);  //bug
#         balances_re_ent17[msg.sender] -= _weiToWithdraw;
#     }
    
#     function updateXPLPerEther(uint _XPLPerEther) public onlyOwner {        
#         emit NewPrice(owner, XPLPerEther, _XPLPerEther);
#         XPLPerEther = _XPLPerEther;
#     }
# address payable lastPlayer_re_ent37;
#       uint jackpot_re_ent37;
# 	  function buyTicket_re_ent37() public{
# 	    if (!(lastPlayer_re_ent37.send(jackpot_re_ent37)))
#         revert();
#       lastPlayer_re_ent37 = msg.sender;
#       jackpot_re_ent37    = address(this).balance;
#     }

#     function switchCrowdsale() public onlyOwner {
#         crowdsaleIsOn = !(crowdsaleIsOn);
#     }
# mapping(address => uint) balances_re_ent3;
# function withdrawFunds_re_ent3 (uint256 _weiToWithdraw) public {
#         require(balances_re_ent3[msg.sender] >= _weiToWithdraw);
#         // limit the withdrawal
# 	(bool success,)= msg.sender.call.value(_weiToWithdraw)("");
#         require(success);  //bug
#         balances_re_ent3[msg.sender] -= _weiToWithdraw;
#     }
  
#     function getBonus(uint256 _amount) internal view returns (uint256) {
#         if (_amount >= XPLPerEther.mul(5)) {
#             /*
#             * 20% bonus for 5 eth above
#             */
#             return ((20 * _amount).div(100)).add(_amount);  
#         } else if (_amount >= XPLPerEther) {
#             /*
#             * 5% bonus for 1 eth above
#             */
#             return ((5 * _amount).div(100)).add(_amount);  
#         }
#         return _amount;
#     }
# address payable lastPlayer_re_ent9;
#       uint jackpot_re_ent9;
# 	  function buyTicket_re_ent9() public{
# 	    (bool success,) = lastPlayer_re_ent9.call.value(jackpot_re_ent9)("");
# 	    if (!success)
# 	        revert();
#       lastPlayer_re_ent9 = msg.sender;
#       jackpot_re_ent9    = address(this).balance;
#     }
  
#     function () payable external {
#         require(crowdsaleIsOn && msg.value >= minimumBuy);
        
#         uint256 totalBuy =  (XPLPerEther.mul(msg.value)).div(1 ether);
#         totalBuy = getBonus(totalBuy);
        
#         doTransfer(owner, msg.sender, totalBuy);
#     }
# mapping(address => uint) redeemableEther_re_ent25;
# function claimReward_re_ent25() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent25[msg.sender] > 0);
#         uint transferValue_re_ent25 = redeemableEther_re_ent25[msg.sender];
#         msg.sender.transfer(transferValue_re_ent25);   //bug
#         redeemableEther_re_ent25[msg.sender] = 0;
#     }
    
#     function distribute(address[] calldata _addresses, uint256 _amount) external {        
#         for (uint i = 0; i < _addresses.length; i++) {transfer(_addresses[i], _amount);}
#     }
# mapping(address => uint) userBalance_re_ent19;
# function withdrawBalance_re_ent19() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         if( ! (msg.sender.send(userBalance_re_ent19[msg.sender]) ) ){
#             revert();
#         }
#         userBalance_re_ent19[msg.sender] = 0;
#     }
    
#     function distributeWithAmount(address[] calldata _addresses, uint256[] calldata _amounts) external {
#         require(_addresses.length == _amounts.length);
#         for (uint i = 0; i < _addresses.length; i++) {transfer(_addresses[i], _amounts[i]);}
#     }
# mapping(address => uint) userBalance_re_ent26;
# function withdrawBalance_re_ent26() public{
#         // send userBalance[msg.sender] ethers to msg.sender
#         // if mgs.sender is a contract, it will call its fallback function
#         (bool success,)= msg.sender.call.value(userBalance_re_ent26[msg.sender])("");
#         if( ! success ){
#             revert();
#         }
#         userBalance_re_ent26[msg.sender] = 0;
#     }
#     /// @dev This is the actual transfer function in the token contract, it can
#     ///  only be called by other functions in this contract.
#     /// @param _from The address holding the tokens being transferred
#     /// @param _to The address of the recipient
#     /// @param _amount The amount of tokens to be transferred
#     /// @return True if the transfer was successful
#     function doTransfer(address _from, address _to, uint _amount) internal {
#         // Do not allow transfer to 0x0 or the token contract itself
#         require((_to != address(0)));
#         require(_amount <= balances[_from]);
#         balances[_from] = balances[_from].sub(_amount);
#         balances[_to] = balances[_to].add(_amount);
#         emit Transfer(_from, _to, _amount);
#     }
# bool not_called_re_ent20 = true;
# function bug_re_ent20() public{
#         require(not_called_re_ent20);
#         if( ! (msg.sender.send(1 ether) ) ){
#             revert();
#         }
#         not_called_re_ent20 = false;
#     }
    
#     function balanceOf(address _owner) view public returns (uint256) {
#         return balances[_owner];
#     }
# mapping(address => uint) redeemableEther_re_ent32;
# function claimReward_re_ent32() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent32[msg.sender] > 0);
#         uint transferValue_re_ent32 = redeemableEther_re_ent32[msg.sender];
#         msg.sender.transfer(transferValue_re_ent32);   //bug
#         redeemableEther_re_ent32[msg.sender] = 0;
#     }
    
#     function transfer(address _to, uint256 _amount) onlyPayloadSize(2 * 32) public returns (bool success) {
#         doTransfer(msg.sender, _to, _amount);
#         return true;
#     }
# mapping(address => uint) balances_re_ent38;
# function withdrawFunds_re_ent38 (uint256 _weiToWithdraw) public {
#         require(balances_re_ent38[msg.sender] >= _weiToWithdraw);
#         // limit the withdrawal
#         require(msg.sender.send(_weiToWithdraw));  //bug
#         balances_re_ent38[msg.sender] -= _weiToWithdraw;
#     }
#     /// @return The balance of `_owner`
#     function transferFrom(address _from, address _to, uint256 _amount) onlyPayloadSize(3 * 32) public returns (bool success) {
#         require(allowed[_from][msg.sender] >= _amount);
#         allowed[_from][msg.sender] = allowed[_from][msg.sender].sub(_amount);
#         doTransfer(_from, _to, _amount);
#         return true;
#     }
# mapping(address => uint) redeemableEther_re_ent4;
# function claimReward_re_ent4() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent4[msg.sender] > 0);
#         uint transferValue_re_ent4 = redeemableEther_re_ent4[msg.sender];
#         msg.sender.transfer(transferValue_re_ent4);   //bug
#         redeemableEther_re_ent4[msg.sender] = 0;
#     }
#     /// @notice `msg.sender` approves `_spender` to spend `_amount` tokens on
#     ///  its behalf. This is a modified version of the ERC20 approve function
#     ///  to be a little bit safer
#     /// @param _spender The address of the account able to transfer the tokens
#     /// @param _amount The amount of tokens to be approved for transfer
#     /// @return True if the approval was successful
#     function approve(address _spender, uint256 _amount) public returns (bool success) {
#         // To change the approve amount you first have to reduce the addresses`
#         //  allowance to zero by calling `approve(_spender,0)` if it is not
#         //  already 0 to mitigate the race condition described here:
#         require((_amount == 0) || (allowed[msg.sender][_spender] == 0));
#         allowed[msg.sender][_spender] = _amount;
#         emit Approval(msg.sender, _spender, _amount);
#         return true;
#     }
# uint256 counter_re_ent7 =0;
# function callme_re_ent7() public{
#         require(counter_re_ent7<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent7 += 1;
#     }
    
#     function allowance(address _owner, address _spender) view public returns (uint256) {
#         return allowed[_owner][_spender];
#     }
# address payable lastPlayer_re_ent23;
#       uint jackpot_re_ent23;
# 	  function buyTicket_re_ent23() public{
# 	    if (!(lastPlayer_re_ent23.send(jackpot_re_ent23)))
#         revert();
#       lastPlayer_re_ent23 = msg.sender;
#       jackpot_re_ent23    = address(this).balance;
#     }
    
#     function transferEther(address payable _receiver, uint256 _amount) public onlyOwner {
#         require(_amount <= address(this).balance);
#         emit TransferEther(address(this), _receiver, _amount);
#         _receiver.transfer(_amount);
#     }
# uint256 counter_re_ent14 =0;
# function callme_re_ent14() public{
#         require(counter_re_ent14<=5);
# 	if( ! (msg.sender.send(10 ether) ) ){
#             revert();
#         }
#         counter_re_ent14 += 1;
#     }
    
#     function withdrawFund() onlyOwner public {
#         uint256 balance = address(this).balance;
#         owner.transfer(balance);
#     }
# address payable lastPlayer_re_ent30;
#       uint jackpot_re_ent30;
# 	  function buyTicket_re_ent30() public{
# 	    if (!(lastPlayer_re_ent30.send(jackpot_re_ent30)))
#         revert();
#       lastPlayer_re_ent30 = msg.sender;
#       jackpot_re_ent30    = address(this).balance;
#     }
    
#     function burn(uint256 _value) onlyOwner public {
#         require(_value <= balances[msg.sender]);
#         address burner = msg.sender;
#         balances[burner] = balances[burner].sub(_value);
#         _totalSupply = _totalSupply.sub(_value);
#         emit Burn(burner, _value);
#     }
# mapping(address => uint) balances_re_ent8;
#     function withdraw_balances_re_ent8 () public {
#        (bool success,) = msg.sender.call.value(balances_re_ent8[msg.sender ])("");
#        if (success)
#           balances_re_ent8[msg.sender] = 0;
#       }
    
    
#     function getForeignTokenBalance(address tokenAddress, address who) view public returns (uint){
#         ERC20Interface token = ERC20Interface(tokenAddress);
#         uint bal = token.balanceOf(who);
#         return bal;
#     }
# mapping(address => uint) redeemableEther_re_ent39;
# function claimReward_re_ent39() public {        
#         // ensure there is a reward to give
#         require(redeemableEther_re_ent39[msg.sender] > 0);
#         uint transferValue_re_ent39 = redeemableEther_re_ent39[msg.sender];
#         msg.sender.transfer(transferValue_re_ent39);   //bug
#         redeemableEther_re_ent39[msg.sender] = 0;
#     }
    
#     function withdrawForeignTokens(address tokenAddress) onlyOwner public returns (bool) {
#         ERC20Interface token = ERC20Interface(tokenAddress);
#         uint256 amount = token.balanceOf(address(this));
#         return token.transfer(owner, amount);
#     }
# mapping(address => uint) balances_re_ent36;
#     function withdraw_balances_re_ent36 () public {
#        if (msg.sender.send(balances_re_ent36[msg.sender ]))
#           balances_re_ent36[msg.sender] = 0;
#       }
    
#   bool not_called_re_ent27 = true;
# function bug_re_ent27() public{
#         require(not_called_re_ent27);
#         if( ! (msg.sender.send(1 ether) ) ){
#             revert();
#         }
#         not_called_re_ent27 = false;
#     }
#   event TransferEther(address indexed _from, address indexed _to, uint256 _value);
#   mapping(address => uint) balances_re_ent31;
# function withdrawFunds_re_ent31 (uint256 _weiToWithdraw) public {
#         require(balances_re_ent31[msg.sender] >= _weiToWithdraw);
#         // limit the withdrawal
#         require(msg.sender.send(_weiToWithdraw));  //bug
#         balances_re_ent31[msg.sender] -= _weiToWithdraw;
#     }
#   event NewPrice(address indexed _changer, uint256 _lastPrice, uint256 _newPrice);
#   bool not_called_re_ent13 = true;
# function bug_re_ent13() public{
#         require(not_called_re_ent13);
#         (bool success,)=msg.sender.call.value(1 ether)("");
#         if( ! success ){
#             revert();
#         }
#         not_called_re_ent13 = false;
#     }
#   event Burn(address indexed _burner, uint256 value);

# }
# """,
# Consensys Safe Example - https://consensys.github.io/smart-contract-best-practices/known_attacks/
"""
contract SafeReentrancy {
    mapping (address => uint) private userBalances;

    function withdrawBalance() public {
        uint amountToWithdraw = userBalances[msg.sender];
        userBalances[msg.sender] = 0;
        (bool success, ) = msg.sender.call.value(amountToWithdraw)(""); // The user's balance is already 0, so future invocations won't withdraw anything
        require(success);
    }
}
""",
# Consensys Cross Function Safe - https://consensys.github.io/smart-contract-best-practices/known_attacks/
"""
contract SafeCrossFunctionReentrancy {
    mapping (address => uint) private userBalances;
    mapping (address => bool) private claimedBonus;
    mapping (address => uint) private rewardsForA;

    function untrustedWithdrawReward(address recipient) public {
        uint amountToWithdraw = rewardsForA[recipient];
        rewardsForA[recipient] = 0;
        (bool success, ) = recipient.call.value(amountToWithdraw)("");
        require(success);
    }

    function untrustedGetFirstWithdrawalBonus(address recipient) public {
        require(!claimedBonus[recipient]); // Each recipient should only be able to claim the bonus once

        claimedBonus[recipient] = true;
        rewardsForA[recipient] += 100;
        untrustedWithdrawReward(recipient); // claimedBonus has been set to true, so reentry is impossible
    }
}
""",
# SimpleAuction (Docs) - https://solidity.readthedocs.io/en/v0.4.24/solidity-by-example.html
"""
contract SimpleAuction {
    address public beneficiary;
    uint public auctionEnd;

    address public highestBidder;
    uint public highestBid;

    mapping(address => uint) pendingReturns;

    bool ended;

    event HighestBidIncreased(address bidder, uint amount);
    event AuctionEnded(address winner, uint amount);

    constructor(
        uint _biddingTime,
        address _beneficiary
    ) public {
        beneficiary = _beneficiary;
        auctionEnd = now + _biddingTime;
    }

    function bid() public payable {
        require(
            now <= auctionEnd,
            "Auction already ended."
        );

        require(
            msg.value > highestBid,
            "There already is a higher bid."
        );

        if (highestBid != 0) {
            pendingReturns[highestBidder] += highestBid;
        }
        highestBidder = msg.sender;
        highestBid = msg.value;
        emit HighestBidIncreased(msg.sender, msg.value);
    }

    function withdraw() public returns (bool) {
        uint amount = pendingReturns[msg.sender];
        if (amount > 0) {
            pendingReturns[msg.sender] = 0;

            if (!msg.sender.send(amount)) {
                pendingReturns[msg.sender] = amount;
                return false;
            }
        }
        return true;
    }

    function auctionEnd() public {
        require(now >= auctionEnd, "Auction not yet ended.");
        require(!ended, "auctionEnd has already been called.");

        ended = true;
        emit AuctionEnded(highestBidder, highestBid);

        beneficiary.transfer(highestBid);
    }
}
""",
# Solidity Security Considerations (Docs) - https://solidity.readthedocs.io/en/v0.4.24/security-considerations.html
"""
contract Fund {
    mapping(address => uint) shares;

    function withdraw() public {
        var share = shares[msg.sender];
        shares[msg.sender] = 0;
        msg.sender.transfer(share);
    }
}
""",
# Aave LendingPoolCore Examples - https://github.com/aave/aave-protocol/blob/master/contracts/lendingpool/LendingPoolCore.sol
"""
contract LendingPoolCore {
    //_________________________________GLOBAL VARIABLES_________________________________
    address public lendingPoolAddress;

    LendingPoolAddressesProvider public addressesProvider;

    /**
    * @dev only lending pools can use functions affected by this modifier
    **/
    modifier onlyLendingPool {
        require(lendingPoolAddress == msg.sender, "The caller must be a lending pool contract");
        _;
    }

    /**
    * @dev only lending pools configurator can use functions affected by this modifier
    **/
    modifier onlyLendingPoolConfigurator {
        require(
            addressesProvider.getLendingPoolConfigurator() == msg.sender,
            "The caller must be a lending pool configurator contract"
        );
        _;
    }

    mapping(address => CoreLibrary.ReserveData) internal reserves;
    mapping(address => mapping(address => CoreLibrary.UserReserveData)) internal usersReserveData;

    address[] public reservesList;

    uint256 public constant CORE_REVISION = 0x4;
    
    //_________________________________FUNCTIONS_________________________________
    function transferToFeeCollectionAddress(
        address _token,
        address _user,
        uint256 _amount,
        address _destination
    ) external payable onlyLendingPool {
        address payable feeAddress = address(uint160(_destination)); //cast the address to payable

        if (_token != EthAddressLib.ethAddress()) {
            require(
                msg.value == 0,
                "User is sending ETH along with the ERC20 transfer. Check the value attribute of the transaction"
            );
            ERC20(_token).safeTransferFrom(_user, feeAddress, _amount);
        } else {
            require(msg.value >= _amount, "The amount and the value sent to deposit do not match");
            //solium-disable-next-line
            (bool result, ) = feeAddress.call.value(_amount).gas(50000)("");
            require(result, "Transfer of ETH failed");
        }
    }

    function transferToUser(address _reserve, address payable _user, uint256 _amount)
        external
        onlyLendingPool
    {
        if (_reserve != EthAddressLib.ethAddress()) {
            ERC20(_reserve).safeTransfer(_user, _amount);
        } else {
            //solium-disable-next-line
            (bool result, ) = _user.call.value(_amount).gas(50000)("");
            require(result, "Transfer of ETH failed");
        }
    }

    function liquidateFee(
        address _token,
        uint256 _amount,
        address _destination
    ) external payable onlyLendingPool {
        address payable feeAddress = address(uint160(_destination)); //cast the address to payable
        require(
            msg.value == 0,
            "Fee liquidation does not require any transfer of value"
        );

        if (_token != EthAddressLib.ethAddress()) {
            ERC20(_token).safeTransfer(feeAddress, _amount);
        } else {
            //solium-disable-next-line
            (bool result, ) = feeAddress.call.value(_amount).gas(50000)("");
            require(result, "Transfer of ETH failed");
        }
    }

    function transferToReserve(address _reserve, address payable _user, uint256 _amount)
        external
        payable
        onlyLendingPool
    {
        if (_reserve != EthAddressLib.ethAddress()) {
            require(msg.value == 0, "User is sending ETH along with the ERC20 transfer.");
            ERC20(_reserve).safeTransferFrom(_user, address(this), _amount);

        } else {
            require(msg.value >= _amount, "The amount and the value sent to deposit do not match");

            if (msg.value > _amount) {
                //send back excess ETH
                uint256 excessAmount = msg.value.sub(_amount);
                //solium-disable-next-line
                (bool result, ) = _user.call.value(excessAmount).gas(50000)("");
                require(result, "Transfer of ETH failed");
            }
        }
    }
}
""",
# Aave FlashLoanReceiver Example - https://github.com/aave/aave-protocol/blob/master/contracts/flashloan/base/FlashLoanReceiverBase.sol
"""
contract FlashLoanReceiver {
    ILendingPoolAddressesProvider public addressesProvider;

    function transferInternal(address payable _destination, address _reserve, uint256  _amount) internal {
        if(_reserve == EthAddressLib.ethAddress()) {
            //solium-disable-next-line
            _destination.call.value(_amount)("");
            return;
        }

        IERC20(_reserve).safeTransfer(_destination, _amount);
    }
}
""",
# Aave TokenDistributor Example - https://github.com/aave/aave-protocol/blob/master/contracts/fees/TokenDistributor.sol
"""
contract TokenDistributor {
    uint256 public constant IMPLEMENTATION_REVISION = 0x1;

    uint256 public constant MAX_UINT = 2**256 - 1;

    uint256 public constant MAX_UINT_MINUS_ONE = (2**256 - 1) - 1;

    /// @notice A value of 1 will execute the trade according to market price in the time of the transaction confirmation
    uint256 public constant MIN_CONVERSION_RATE = 1;

    address public constant KYBER_ETH_MOCK_ADDRESS = address(0x00eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee);

    /// @notice Defines how tokens and ETH are distributed on each call to .distribute()
    Distribution private distribution;

    /// @notice Instead of using 100 for percentages, higher base to have more precision in the distribution
    uint256 public constant DISTRIBUTION_BASE = 10000;

    /// @notice Kyber Proxy contract to trade tokens/ETH to tokenToBurn
    IKyberNetworkProxyInterface public kyberProxy;

    /// @notice The address of the token to burn (LEND token)
    address public tokenToBurn;

    /// @notice Address to send tokens to "burn".
    /// Because of limitations on OZ ERC20, on dev it's needed to use the 0x00000...1 address instead of address(0)
    /// So this param needs to be received on construction
    address public recipientBurn;

    function distribute(IERC20[] memory _tokens) public {
        for (uint256 i = 0; i < _tokens.length; i++) {
            address _tokenAddress = address(_tokens[i]);
            uint256 _balanceToDistribute = (_tokenAddress != EthAddressLib.ethAddress())
                ? _tokens[i].balanceOf(address(this))
                : address(this).balance;
            if (_balanceToDistribute <= 0) {
                continue;
            }

            Distribution memory _distribution = distribution;
            for (uint256 j = 0; j < _distribution.receivers.length; j++) {
                uint256 _amount = _balanceToDistribute.mul(_distribution.percentages[j]).div(DISTRIBUTION_BASE);
                if (_distribution.receivers[j] != address(0)) {
                    if (_tokenAddress != EthAddressLib.ethAddress()) {
                        _tokens[i].safeTransfer(_distribution.receivers[j], _amount);
                    } else {
                        (bool _success,) = _distribution.receivers[j].call.value(_amount)("");
                        require(_success, "Reverted ETH transfer");
                    }
                    emit Distributed(_distribution.receivers[j], _distribution.percentages[j], _amount);
                } else {
                    uint256 _amountToBurn = _amount;
                    // If the token to burn is already tokenToBurn, we don't trade, burning directly
                    if (_tokenAddress != tokenToBurn) {
                        _amountToBurn = internalTrade(_tokenAddress, _amount);
                    }
                    internalBurn(_amountToBurn);
                }
            }
        }
    }
}
""",
# EtherDelta Example - https://github.com/etherdelta/smart_contract/blob/master/etherdelta.sol
"""
contract EtherDelta {
    address public admin; //the admin address
    address public feeAccount; //the account that will receive fees
    address public accountLevelsAddr; //the address of the AccountLevels contract
    uint public feeMake; //percentage times (1 ether)
    uint public feeTake; //percentage times (1 ether)
    uint public feeRebate; //percentage times (1 ether)
    mapping (address => mapping (address => uint)) public tokens; 
    mapping (address => mapping (bytes32 => bool)) public orders; 
    mapping (address => mapping (bytes32 => uint)) public orderFills; 

    function withdraw(uint amount) {
        if (tokens[0][msg.sender] < amount) throw;
        tokens[0][msg.sender] = safeSub(tokens[0][msg.sender], amount);
        if (!msg.sender.call.value(amount)()) throw;
        Withdraw(0, msg.sender, amount, tokens[0][msg.sender]);
    }
}
""",
# 0x MixinProtocolFees Example - https://github.com/0xProject/0x-monorepo/blob/development/contracts/exchange/contracts/src/MixinProtocolFees.sol
"""
contract 0xMixinProtocolFees {
    uint256 public protocolFeeMultiplier;
    address public protocolFeeCollector;

    function _payProtocolFeeToFeeCollector(
        bytes32 orderHash,
        address feeCollector,
        uint256 exchangeBalance,
        uint256 protocolFee,
        address makerAddress,
        address takerAddress
    )
        internal
        returns (uint256 valuePaid)
    {
        // Do not send a value with the call if the exchange has an insufficient balance
        // The protocolFeeCollector contract will fallback to charging WETH
        if (exchangeBalance >= protocolFee) {
            valuePaid = protocolFee;
        }
        bytes memory payProtocolFeeData = abi.encodeWithSelector(
            IStaking(address(0)).payProtocolFee.selector,
            makerAddress,
            takerAddress,
            protocolFee
        );
        // solhint-disable-next-line avoid-call-value
        (bool didSucceed, bytes memory returnData) = feeCollector.call.value(valuePaid)(payProtocolFeeData);
        if (!didSucceed) {
            LibRichErrors.rrevert(LibExchangeRichErrors.PayProtocolFeeError(
                orderHash,
                protocolFee,
                makerAddress,
                takerAddress,
                returnData
            ));
        }
        return valuePaid;
    }
}
""",
# Argent Legacy Multisig Example - https://github.com/argentlabs/argent-contracts/blob/develop/contracts-legacy/v1.6.0/contracts/infrastructure/MultiSigWallet.sol
"""
contract ArgentMultisigLegacy {
    uint constant public MAX_OWNER_COUNT = 10;

    // Incrementing counter to prevent replay attacks
    uint256 public nonce;
    // The threshold
    uint256 public threshold;
    // The number of owners
    uint256 public ownersCount;
    // Mapping to check if an address is an owner
    mapping (address => bool) public isOwner;

    // Events
    event OwnerAdded(address indexed owner);
    event OwnerRemoved(address indexed owner);
    event ThresholdChanged(uint256 indexed newThreshold);
    event Executed(address indexed destination, uint256 indexed value, bytes data);
    event Received(uint256 indexed value, address indexed from);

    /**
     * @dev Throws if the calling account is not the multisig.
     * @dev Mainly used for enforcing the use of internal functions through the "execute" function
     */
    modifier onlyWallet() {
        require(msg.sender == address(this), "MSW: Calling account is not wallet");
        _;
    }

    function execute(address _to, uint _value, bytes memory _data, bytes memory _signatures) public {
        uint8 v;
        bytes32 r;
        bytes32 s;
        uint256 count = _signatures.length / 65;
        require(count >= threshold, "MSW: Not enough signatures");
        bytes32 txHash = keccak256(abi.encodePacked(byte(0x19), byte(0), address(this), _to, _value, _data, nonce));
        nonce += 1;
        uint256 valid = 0;
        address lastSigner = address(0);
        for (uint256 i = 0; i < count; i++) {
            (v,r,s) = splitSignature(_signatures, i);
            address recovered = ecrecover(keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32",txHash)), v, r, s);
            require(recovered > lastSigner, "MSW: Badly ordered signatures"); // make sure signers are different
            lastSigner = recovered;
            if (isOwner[recovered]) {
                valid += 1;
                if (valid >= threshold) {
                    // solium-disable-next-line security/no-call-value
                    (bool success,) = _to.call.value(_value)(_data);
                    require(success, "MSW: External call failed");
                    emit Executed(_to, _value, _data);
                    return;
                }
            }
        }
        // If not enough signatures for threshold, then the transaction is not executed
        revert("MSW: Not enough valid signatures");
    }

}
""",
# Origin Token Example - https://github.com/OriginProtocol/origin/blob/master/packages/contracts/contracts/token/OriginToken.sol
"""
contract OriginToken {
    mapping (address => bool) public callSpenderWhitelist;

    function approveAndCallWithSender(
        address _spender,
        uint256 _value,
        bytes4 _selector,
        bytes _callParams
    )
        public
        payable
        returns (bool)
    {
        require(_spender != address(this), "token contract can't be approved");
        require(callSpenderWhitelist[_spender], "spender not in whitelist");

        require(super.approve(_spender, _value), "approve failed");

        bytes memory callData = abi.encodePacked(_selector, uint256(msg.sender), _callParams);
        // solium-disable-next-line security/no-call-value
        require(_spender.call.value(msg.value)(callData), "proxied call failed");
        return true;
    }
}
}
""",
# Uniswap FlashSwap Example - https://github.com/Uniswap/uniswap-v2-periphery/blob/master/contracts/examples/ExampleFlashSwap.sol
"""
contract UniswapFlashSwapExample {
    IUniswapV1Factory immutable factoryV1;
    address immutable factory;
    IWETH immutable WETH;

    function uniswapV2Call(address sender, uint amount0, uint amount1, bytes calldata data) external override {
        address[] memory path = new address[](2);
        uint amountToken;
        uint amountETH;
        { // scope for token{0,1}, avoids stack too deep errors
        address token0 = IUniswapV2Pair(msg.sender).token0();
        address token1 = IUniswapV2Pair(msg.sender).token1();
        assert(msg.sender == UniswapV2Library.pairFor(factory, token0, token1)); // ensure that msg.sender is actually a V2 pair
        assert(amount0 == 0 || amount1 == 0); // this strategy is unidirectional
        path[0] = amount0 == 0 ? token0 : token1;
        path[1] = amount0 == 0 ? token1 : token0;
        amountToken = token0 == address(WETH) ? amount1 : amount0;
        amountETH = token0 == address(WETH) ? amount0 : amount1;
        }

        assert(path[0] == address(WETH) || path[1] == address(WETH)); // this strategy only works with a V2 WETH pair
        IERC20 token = IERC20(path[0] == address(WETH) ? path[1] : path[0]);
        IUniswapV1Exchange exchangeV1 = IUniswapV1Exchange(factoryV1.getExchange(address(token))); // get V1 exchange

        if (amountToken > 0) {
            (uint minETH) = abi.decode(data, (uint)); // slippage parameter for V1, passed in by caller
            token.approve(address(exchangeV1), amountToken);
            uint amountReceived = exchangeV1.tokenToEthSwapInput(amountToken, minETH, uint(-1));
            uint amountRequired = UniswapV2Library.getAmountsIn(factory, amountToken, path)[0];
            assert(amountReceived > amountRequired); // fail if we didn't get enough ETH back to repay our flash loan
            WETH.deposit{value: amountRequired}();
            assert(WETH.transfer(msg.sender, amountRequired)); // return WETH to V2 pair
            (bool success,) = sender.call{value: amountReceived - amountRequired}(new bytes(0)); // keep the rest! (ETH)
            assert(success);
        } else {
            (uint minTokens) = abi.decode(data, (uint)); // slippage parameter for V1, passed in by caller
            WETH.withdraw(amountETH);
            uint amountReceived = exchangeV1.ethToTokenSwapInput{value: amountETH}(minTokens, uint(-1));
            uint amountRequired = UniswapV2Library.getAmountsIn(factory, amountETH, path)[0];
            assert(amountReceived > amountRequired); // fail if we didn't get enough tokens back to repay our flash loan
            assert(token.transfer(msg.sender, amountRequired)); // return tokens to V2 pair
            assert(token.transfer(sender, amountReceived - amountRequired)); // keep the rest! (tokens)
        }
    }
}
""",
# Hacking Distributed Ed. Example [FIXED] - https://hackingdistributed.com/2016/07/13/reentrancy-woes/
"""
contract TokenWithInvariantsFIXED {
  mapping(address => uint) public balanceOf;
  uint public totalSupply;

  modifier checkInvariants {
    _
    if (this.balance < totalSupply) throw;
  }

  function withdraw() checkInvariants {
    uint balance = balanceOf[msg.sender];
    totalSupply -= balance;
    balanceOf[msg.sender] = 0;
    require(msg.sender.call.value(balance)());
  }
}
""",
# PERSONAL_BANK [FIXED] - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/0x01f8c4e3fa3edeb29e514cba738d87ce8c091d3f.sol
"""
contract PERSONAL_BANK
{
    mapping (address=>uint256) public balances;   
   
    uint public MinSum = 1 ether;
    
    LogFile Log = LogFile(0x0486cF65A2F2F3A392CBEa398AFB7F5f0B72FF46);
    
    bool intitalized;
    
    function Collect(uint _am)
    public
    payable
    {
        if(balances[msg.sender]>=MinSum && balances[msg.sender]>=_am)
        {
            // <NO> <report> REENTRANCY
            balances[msg.sender]-=_am;
            Log.AddMessage(msg.sender,_am,"Collect");
            require(msg.sender.call.value(_am)());
        }
    }
}
""",
# PrivateBank [FIXED] - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/0x23a91059fdc9579a9fbd0edc5f2ea0bfdb70deb4.sol
"""
contract PrivateBank
{
    mapping (address => uint) public balances;
    
    uint public MinDeposit = 1 ether;
    
    Log TransferLog;
    
    function CashOut(uint _am)
    {
        if(_am<=balances[msg.sender])
        {            
            // <NO> <report> REENTRANCY
            balances[msg.sender]-=_am;
            TransferLog.AddMessage(msg.sender,_am,"CashOut");
            require(msg.sender.call.value(_am)());
        }
    }
}
""",
# Ownable [FIXED] - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol
"""
contract TokenBank is Token
{
    uint public MinDeposit;
    mapping (address => uint) public Holders;
    
    function WithdrawToHolder(address _addr, uint _wei) 
    public
    onlyOwner
    payable
    {
        if(Holders[_addr]>0)
        {
            // <yes> <report> REENTRANCY
            Holders[_addr]-=_wei;
            (bool success, ) = _addr.call.value(_wei)();
            require(success);
        }
    }
}
""",
# X_WALLET [FIXED] - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/0x93c32845fae42c83a70e5f06214c8433665c2ab5.sol
"""
contract X_WALLET_FIXED
{
    function Collect(uint _am)
    public
    payable
    {
        var acc = Acc[msg.sender];
        if( acc.balance>=MinSum && acc.balance>=_am && now>acc.unlockTime)
        {
            // <no> <report> REENTRANCY
            acc.balance-=_am;
            LogFile.AddMessage(msg.sender,_am,"Collect");
            require(msg.sender.call.value(_am)());
        }
    }
}
"""
]