from browser_use import Agent
# from browser_use.llm.anthropic.chat import ChatAnthropic
from browser_use.llm.openai.chat import ChatOpenAI

llm = ChatOpenAI(
  model="anthropic/claude-opus-4",
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
  temperature=0.2,
)

Agent('go to ds160 us visa form and solve the captcha and fill out the form with dummy data', llm=llm).run_sync()