
reentrancyList = [
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
    # 0x01f8c4e3fa3edeb29e514cba738d87ce8c091d3f
    """
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
    """,
    # 0x23a91059fdc9579a9fbd0edc5f2ea0bfdb70deb4
    """
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
    """,
    # 0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839
    """
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
    """,
    # 0x93c32845fae42c83a70e5f06214c8433665c2ab5
    """
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
    """
    # 0x941d225236464a25eb18076df7da6a91d0f95e9e,
    """
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
    """,
    # etherbank
    """
        function withdrawBalance() {  
            uint amountToWithdraw = userBalances[msg.sender];
            // <yes> <report> REENTRANCY
            if (!(msg.sender.call.value(amountToWithdraw)())) { throw; }
            userBalances[msg.sender] = 0;
        }   
    """,
    # etherstore
    """
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
    """,
    # modifier_reentrancy
    """
        modifier hasNoBalance {
            require(tokenBalance[msg.sender] == 0);
            _;
        }
        function airDrop() hasNoBalance supportsToken  public{
            tokenBalance[msg.sender] += 20;
        }
    """,
    # reentrance
    """
        function withdraw(uint _amount) public {
            if(balances[msg.sender] >= _amount) {
            // <yes> <report> REENTRANCY
            if(msg.sender.call.value(_amount)()) {
                _amount;
            }
            balances[msg.sender] -= _amount;
            }
        }
    """
    # reetrancy_bonus
    """
        function getFirstWithdrawalBonus(address recipient) public {
            require(!claimedBonus[recipient]); // Each recipient should only be able to claim the bonus once

            rewardsForA[recipient] += 100;
            // <yes> <report> REENTRANCY
            withdrawReward(recipient); // At this point, the caller will be able to execute getFirstWithdrawalBonus again.
            claimedBonus[recipient] = true;
        }
    """,
    # reentrancy_cross_function
    """
        function withdrawBalance() public {
            uint amountToWithdraw = userBalances[msg.sender];
            // <yes> <report> REENTRANCY
            (bool success, ) = msg.sender.call.value(amountToWithdraw)(""); // At this point, the caller's code is executed, and can call transfer()
            require(success);
            userBalances[msg.sender] = 0;
        }
    """,
    # reentrancy_dao
    """
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
    """
    # reentrancy_insecure
    """
        function withdrawBalance() public {
            uint amountToWithdraw = userBalances[msg.sender];
            // <yes> <report> REENTRANCY
            (bool success, ) = msg.sender.call.value(amountToWithdraw)(""); // At this point, the caller's code is executed, and can call withdrawBalance again
            require(success);
            userBalances[msg.sender] = 0;
        }
    """
    # reetrancy_simple
    """
        function withdrawBalance(){
            // send userBalance[msg.sender] ethers to msg.sender
            // if mgs.sender is a contract, it will call its fallback function
            // <yes> <report> REENTRANCY
            if( ! (msg.sender.call.value(userBalance[msg.sender])() ) ){
                throw;
            }
            userBalance[msg.sender] = 0;
        }
    """,
    # simple_dao
    """
        function withdraw(uint amount) {
            if (credit[msg.sender]>= amount) {
            // <yes> <report> REENTRANCY
            bool res = msg.sender.call.value(amount)();
            credit[msg.sender]-=amount;
            }
        }
    """,
    # spank_chain_payment
    """
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
    """
]