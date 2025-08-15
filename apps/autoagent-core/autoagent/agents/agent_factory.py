# In agent-mono/agents/agent_factory.py
import dill  # For serializing Python objects

def clone_agent(original_agent, new_name):
    """Create editable copy of an agent"""
    agent_copy = dill.loads(dill.dumps(original_agent))
    agent_copy.name = new_name
    agent_copy.memory = []  # Reset memory
    return agent_copy
