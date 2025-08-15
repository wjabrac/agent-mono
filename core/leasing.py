# In agent-mono/core/leasing.py
class TimeLease:
    def __init__(self, agent, owner_wallet):
        self.agent = agent
        self.owner = owner_wallet  # Crypto address
        self.rate_per_sec = 0.0001  # ETH/sec

    def execute(self, task, payer_wallet):
        # Pseudocode: Verify payment via web3
        if verify_payment(payer_wallet, self.owner, self.rate_per_sec):
            return self.agent.run(task)
