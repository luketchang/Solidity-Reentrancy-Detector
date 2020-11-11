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
# MyAugmented____
"""
contract MyAugmented {
    mapping(address => uint) balances;
    mapping(address => bool) winners;
    uint gameReward = 50;

    modifier registered() {
        require(balances[msg.sender] != 0);
        _;
    }

    function withdrawFunds (uint256 _weiToWithdraw) public registered {
        require(balances[msg.sender] >= _weiToWithdraw);
        (bool success,) = msg.sender.call.value(_weiToWithdraw)("");
        require(success);
        balances[msg.sender] -= _weiToWithdraw;
    }

    function safeWithdrawFunds(uint256 amount) public registered {
        require(balances[msg.sender] >= _weiToWithdraw);
        balances[msg.sender] -= _weiToWithdraw;
        (bool success,) = msg.sender.call.value(_weiToWithdraw)("");
        require(success);
    }

    function claimReward() registered {
        bool isWinner = winners[msg.sender];
        require(isWinner);
        bool hasMoney = balances[msg.sender] > 5;
        require(hasMoney);

        require(msg.sender.call.value(gameReward)());
        winners[msg.sender] = false;
    }
}
""",
# EtherDelta Example [POSITIVE] - https://github.com/etherdelta/smart_contract/blob/master/etherdelta.sol
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
        if (!msg.sender.call.value(amount)()) throw;
        tokens[0][msg.sender] = safeSub(tokens[0][msg.sender], amount);
        Withdraw(0, msg.sender, amount, tokens[0][msg.sender]);
    }
}
""",
# ____________________________________________SPLIT_(31/255)________________________________________________
# SolidiFI 39 - https://github.com/smartbugs/SolidiFI-benchmark/blob/master/buggy_contracts/Re-entrancy/buggy_39.sol
"""
contract TAMCContract {
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
# ____________________________________________________POSITIVES-->NEGATIVES___________________________________________________________
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
""",
# EtherStore [FIXED] - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/etherstore.sol
"""
contract EtherStore {

    uint256 public withdrawalLimit = 1 ether;
    mapping(address => uint256) public lastWithdrawTime;
    mapping(address => uint256) public balances;

    function withdrawFunds (uint256 _weiToWithdraw) public {
        require(balances[msg.sender] >= _weiToWithdraw);
        // limit the withdrawal
        require(_weiToWithdraw <= withdrawalLimit);
        // limit the time allowed to withdraw
        require(now >= lastWithdrawTime[msg.sender] + 1 weeks);
        // <no> <report> REENTRANCY
        balances[msg.sender] -= _weiToWithdraw;
        lastWithdrawTime[msg.sender] = now;
        require(msg.sender.call.value(_weiToWithdraw)());
    }
}
""",
# Reetrance [FIXED] - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/reentrance.sol
"""
contract Reentrance {
  mapping(address => uint) public balances;

  function withdraw(uint _amount) public {
    if(balances[msg.sender] >= _amount) {
      // <no> <report> REENTRANCY
      balances[msg.sender] -= _amount;
      if(msg.sender.call.value(_amount)()) {
        _amount;
      }
    }
  }
}
""",
# reentrancy_bonus [FIXED]- https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/reentrancy_bonus.sol
"""
contract Reentrancy_bonus{
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
        // <no> <report> REENTRANCY
        claimedBonus[recipient] = true;
        withdrawReward(recipient); // At this point, the caller will be able to execute getFirstWithdrawalBonus again.
    }
}
""",
# Reentrancy_cross_function [FIXED] - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/reentrancy_cross_function.sol
"""
contract Reentrancy_cross_function {
    mapping (address => uint) private userBalances;

    function withdrawBalance() public {
        uint amountToWithdraw = userBalances[msg.sender];
        // <no> <report> REENTRANCY
        userBalances[msg.sender] = 0;
        (bool success, ) = msg.sender.call.value(amountToWithdraw)(""); // At this point, the caller's code is executed, and can call transfer()
        require(success);
    }
}
""",
# ReentrancyDAO [FIXED] - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/reentrancy_dao.sol
"""
contract ReentrancyDAO {
    mapping (address => uint) credit;
    uint balance;

    function withdrawAll() public {
        uint oCredit = credit[msg.sender];
        if (oCredit > 0) {
            balance -= oCredit;
            // <no> <report> REENTRANCY
            credit[msg.sender] = 0;
            bool callResult = msg.sender.call.value(oCredit)();
            require (callResult);
        }
    }
}
""",
# Reentrancy_insecure [FIXED] - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/reentrancy_insecure.sol
"""
contract Reentrancy_insecure {
    mapping (address => uint) private userBalances;

    function withdrawBalance() public {
        uint amountToWithdraw = userBalances[msg.sender];
        // <no> <report> REENTRANCY
        userBalances[msg.sender] = 0;
        (bool success, ) = msg.sender.call.value(amountToWithdraw)(""); // At this point, the caller's code is executed, and can call withdrawBalance again
        require(success);
    }
}
""",
# reentrancy_simple [FIXED] - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/reentrancy_simple.sol
"""
contract Reentrance {
     mapping (address => uint) userBalance;

     function withdrawBalance(){
         // send userBalance[msg.sender] ethers to msg.sender
         // if mgs.sender is a contract, it will call its fallback function
         // <no> <report> REENTRANCY
         userBalance[msg.sender] = 0;
         if( ! (msg.sender.call.value(userBalance[msg.sender])() ) ){
             throw;
         }
     }
 }
""",
# SimpleDAO [FIXED] - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/simple_dao.sol
"""
contract SimpleDAO {
  mapping (address => uint) public credit;

  function withdraw(uint amount) {
    if (credit[msg.sender]>= amount) {
      // <no> <report> REENTRANCY
      credit[msg.sender]-=amount;
      bool res = msg.sender.call.value(amount)();
    }
  }
}
""",
# LedgerChannel (spankchain) [FIXED] - https://github.com/smartbugs/smartbugs/blob/master/dataset/reentrancy/spank_chain_payment.sol
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

    function LCOpenTimeout(bytes32 _lcID) public {
        require(msg.sender == Channels[_lcID].partyAddresses[0] && Channels[_lcID].isOpen == false);
        require(now > Channels[_lcID].LCopenTimeout);

        if(Channels[_lcID].initialDeposit[0] != 0) {
            // <no> <report> REENTRANCY
            Channels[_lcID].initialDeposit[0] = 0;
            Channels[_lcID].partyAddresses[0].transfer(Channels[_lcID].ethBalances[0]);
        }
        if(Channels[_lcID].initialDeposit[1] != 0) {
            // <no> <report> REENTRANCY
            Channels[_lcID].initialDeposit[1] = 0;
            require(Channels[_lcID].token.transfer(Channels[_lcID].partyAddresses[0], Channels[_lcID].erc20Balances[0]),"CreateChannel: token transfer failure");
        }

        emit DidLCClose(_lcID, 0, Channels[_lcID].ethBalances[0], Channels[_lcID].erc20Balances[0], 0, 0);

        // only safe to delete since no action was taken on this channel
        delete Channels[_lcID];
    }
}
""",
# Victim [FIXED] - https://github.com/ltchang2019/GraphDeeSmartContract/blob/master/contract_data/reentrancy/source_code/Victim.sol
"""
contract Victim {
   
  mapping(address => uint) public balances;
   
  function withdraw(uint _amount) public {
        if(balances[msg.sender] >= _amount) {
            balances[msg.sender] -= _amount;
            if(msg.sender.call.value(_amount)()) {
                _amount;
            }
        }
    }
}
""",
# DumbDAO [FIXED] - https://github.com/ltchang2019/GraphDeeSmartContract/blob/master/contract_data/reentrancy/source_code/dumbDAO.sol
"""
contract dumbDAO {
  event PaymentCalled(address payee, uint amount);
  event TokensBought(address buyer, uint amount);
  event TokensTransfered(address from, address to, uint amount);
  event InsufficientFunds(uint bal, uint amount);

  mapping (address => uint) public balances;

  function withdraw(address _recipient) returns (bool) {
    if (balances[msg.sender] == 0){
        InsufficientFunds(balances[msg.sender],balances[msg.sender]);
        throw;
    }
    PaymentCalled(_recipient, balances[msg.sender]);

    balances[msg.sender] = 0;
    if (_recipient.call.value(balances[msg.sender])()) {  
        return true;
    }
  }
}
""",
# SendBalance [FIXED] - https://github.com/ltchang2019/GraphDeeSmartContract/blob/master/contract_data/reentrancy/source_code/SendBalance.sol
"""
contract SendBalance {
 mapping (address => uint) userBalances ;
 bool withdrawn = false ;
 
 function withdrawBalance(){
     userBalances[msg.sender] = 0;
    if (!(msg.sender.call.value(userBalances[msg.sender])())) { throw ; }
 }
}
""",
# Reetrance_01 [FIXED] - https://github.com/ltchang2019/GraphDeeSmartContract/blob/master/contract_data/reentrancy/source_code/Reentrance_01.sol
"""
contract Reentrance {
    mapping (address => uint) userBalance;

    function withdrawBalance(){
        userBalance[msg.sender] = 0;
        if(!(msg.sender.call.value(userBalance[msg.sender])())){
            throw;
        }
    }
}
""",
# Reentrance_02 [FIXED] - https://github.com/ltchang2019/GraphDeeSmartContract/blob/master/contract_data/reentrancy/source_code/Reentrance_02.sol
"""
contract Reentrance {
  mapping(address => uint) public balances;

    function withdraw(uint _amount) public {
        if(balances[msg.sender] >= _amount) {
            balances[msg.sender] -= _amount;
            if(msg.sender.call.value(_amount)()) {
                _amount;
            }
        }
    }
}
""",
# ____________________________________________________NEGATIVES-->POSITIVES___________________________________________________________
# Consensys Safe Example [POSITIVE] - https://consensys.github.io/smart-contract-best-practices/known_attacks/
"""
contract SafeReentrancy {
    mapping (address => uint) private userBalances;

    function withdrawBalance() public {
        uint amountToWithdraw = userBalances[msg.sender];
        if(amountToWithdraw > 0) {
            require(msg.sender.call.value(amountToWithdraw)("")); // The user's balance is already 0, so future invocations won't withdraw anything
            userBalances[msg.sender] = 0;
        }
    }
}
""",
# Consensys Cross Function Safe [POSITIVE] - https://consensys.github.io/smart-contract-best-practices/known_attacks/
"""
contract SafeCrossFunctionReentrancy {
    mapping (address => uint) private userBalances;
    mapping (address => bool) private claimedBonus;
    mapping (address => uint) private rewardsForA;

    function untrustedWithdrawReward(address recipient) public {
        uint amountToWithdraw = rewardsForA[recipient];
        (bool success, ) = recipient.call.value(amountToWithdraw)("");
        require(success);
        rewardsForA[recipient] = 0;
    }

    function untrustedGetFirstWithdrawalBonus(address recipient) public {
        require(!claimedBonus[recipient]); // Each recipient should only be able to claim the bonus once

        claimedBonus[recipient] = true;
        rewardsForA[recipient] += 100;
        untrustedWithdrawReward(recipient); // claimedBonus has been set to true, so reentry is impossible
    }
}
""",
# SimpleAuction (Docs) [POSITIVE] - https://solidity.readthedocs.io/en/v0.4.24/solidity-by-example.html
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

    function withdraw() public returns (bool) {
        uint amount = pendingReturns[msg.sender];
        if (amount > 0) {
            if (!msg.sender.send(amount)) {
                pendingReturns[msg.sender] = amount;
                return false;
            }
        }
        pendingReturns[msg.sender] = 0;
        return true;
    }
}
""",
# Solidity Security Considerations (Docs) [POSITIVE] - https://solidity.readthedocs.io/en/v0.4.24/security-considerations.html
"""
contract Fund {
    mapping(address => uint) shares;

    function withdraw() public {
        var share = shares[msg.sender];
        (bool success, ) = msg.sender.transfer(share);
        require(success);
        shares[msg.sender] = 0;
    }
}
""",
# ____________________________________________________SELF_AUGMENTED___________________________________________________________
]