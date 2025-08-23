"""
Optimal DS160 form filling using the best OpenRouter models for 2025
- GPT-4o for balanced vision + text performance
- Minimal latency and maximum accuracy
- Fixed URL issues
"""

import asyncio
import os
import json
from datetime import datetime
from pathlib import Path
from browser_use import Agent
from browser_use.browser.profile import BrowserProfile
from browser_use.llm import ChatOpenAI

class SimpleLearningSystem:
	"""
	Simple learning system that prevents repeating the same mistakes
	"""
	
	def __init__(self, memory_file="ds160_learning_memory.json"):
		self.memory_file = Path(memory_file)
		self.memory = self.load_memory()
	
	def load_memory(self):
		"""Load learning memory from file"""
		if self.memory_file.exists():
			try:
				with open(self.memory_file, 'r') as f:
					return json.load(f)
			except:
				pass
		return {
			"failed_element_patterns": [],
			"successful_sequences": [],
			"element_dependencies": {},
			"common_errors": {}
		}
	
	def save_memory(self):
		"""Save learning memory to file"""
		with open(self.memory_file, 'w') as f:
			json.dump(self.memory, f, indent=2)
	
	def record_failed_element(self, element_index, error_msg, page_context):
		"""Record a failed element interaction"""
		failure = {
			"element_index": element_index,
			"error": error_msg,
			"page_context": page_context[:200],  # First 200 chars of page content
			"timestamp": datetime.now().isoformat()
		}
		
		self.memory["failed_element_patterns"].append(failure)
		
		# Keep only last 50 failures to prevent memory bloat
		if len(self.memory["failed_element_patterns"]) > 50:
			self.memory["failed_element_patterns"] = self.memory["failed_element_patterns"][-50:]
		
		self.save_memory()
	
	def record_successful_sequence(self, sequence):
		"""Record a successful interaction sequence"""
		success = {
			"sequence": sequence,
			"timestamp": datetime.now().isoformat()
		}
		
		self.memory["successful_sequences"].append(success)
		
		# Keep only last 20 successful sequences
		if len(self.memory["successful_sequences"]) > 20:
			self.memory["successful_sequences"] = self.memory["successful_sequences"][-20:]
		
		self.save_memory()
	
	def record_dependency(self, prerequisite_element, dependent_element, relationship):
		"""Record element dependencies (e.g., must fill A before B becomes accessible)"""
		key = f"{prerequisite_element}->{dependent_element}"
		self.memory["element_dependencies"][key] = {
			"prerequisite": prerequisite_element,
			"dependent": dependent_element,
			"relationship": relationship,
			"timestamp": datetime.now().isoformat()
		}
		self.save_memory()
	
	def get_learning_insights(self):
		"""Generate insights from learning memory for system message"""
		insights = []
		
		# Analyze failed patterns
		if self.memory["failed_element_patterns"]:
			recent_failures = self.memory["failed_element_patterns"][-10:]
			common_errors = {}
			for failure in recent_failures:
				error_type = failure["error"][:50]  # First 50 chars of error
				common_errors[error_type] = common_errors.get(error_type, 0) + 1
			
			most_common = max(common_errors, key=common_errors.get) if common_errors else None
			if most_common:
				insights.append(f"LEARNED: Avoid pattern '{most_common}' - occurred {common_errors[most_common]} times recently")
		
		# Analyze successful patterns
		if self.memory["successful_sequences"]:
			insights.append(f"LEARNED: {len(self.memory['successful_sequences'])} successful interaction patterns recorded")
		
		# Analyze dependencies
		if self.memory["element_dependencies"]:
			insights.append("LEARNED: Element dependencies discovered - some fields require prerequisites")
			for key, dep in list(self.memory["element_dependencies"].items())[-5:]:  # Last 5
				insights.append(f"  - {dep['prerequisite']} must be completed before {dep['dependent']}")
		
		return insights

async def test_optimal_ds160():
	"""
	Test DS160 form filling with optimal 2025 models via OpenRouter + Simple Learning System
	"""
	
	# Initialize learning system
	learning_system = SimpleLearningSystem()
	learning_insights = learning_system.get_learning_insights()
	
	print("🚀 DS160 Form Filling - Optimal 2025 Setup")
	print("=" * 60)
	print("🧠👁️ Using Qwen2.5-VL-32B for superior vision capabilities")
	print("⚡ Optimized for minimal latency and maximum accuracy")
	print("🔗 Via OpenRouter unified API")
	print("🎓 Simple Learning System: Prevents repeating mistakes")
	print("=" * 60)
	
	if learning_insights:
		print("📚 Learning Insights:")
		for insight in learning_insights:
			print(f"   {insight}")
		print("=" * 60)
	
	# Create Qwen2.5-VL model via OpenRouter - BEST VISION for captcha
	llm = ChatOpenAI(
		model="qwen/qwen2.5-vl-32b-instruct",
		base_url="https://openrouter.ai/api/v1",
		api_key="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",
		temperature=0.1
	)
	
	# Browser profile for visible automation
	profile = BrowserProfile(
		headless=False,
		disable_security=True,
		browser_type="chromium",
		viewport={"width": 1280, "height": 1024},
		args=[
			"--force-device-scale-factor=1.50",  # 150% zoom
			"--high-dpi-support=1",
			"--device-scale-factor=1.25",
			"--disable-beforeunload-throttling",  # Disable beforeunload popups
			"--disable-popup-blocking",  # Disable popup blocking
			"--disable-prompt-on-repost"  # Disable repost prompts
		]
	)
	
	# Build enhanced system message with learning insights
	learning_context = ""
	if learning_insights:
		learning_context = "\n\nLEARNING INSIGHTS (Avoid previous mistakes):\n" + "\n".join(f"- {insight}" for insight in learning_insights)
	
	# Optimized system message for Qwen2.5-VL with learning
	system_message = f"""
	You are an expert DS160 visa application form filler using Qwen2.5-VL with superior vision capabilities for captcha solving.{learning_context}
	
	TASK SEQUENCE (IMPORTANT - FOLLOW THIS ORDER):
	1. Navigate to DS160 website: https://ceac.state.gov/genniv/
	2. FIRST: Select embassy location from dropdown (e.g., "CANADA, TORONTO")
	3. THEN: Solve the captcha using your superior vision capabilities
	4. Click "START AN APPLICATION" button
	5. CRITICAL CHECKPOINT: Look for and complete ALL required elements on current page
	   - Check for unchecked checkboxes (agreements, terms, acknowledgments)
	   - Verify all required fields are filled
	   - Look for "I agree" or similar checkboxes that must be checked
	6. Fill all personal information sections with realistic test data
	7. Complete travel details and background questions
	8. Save progress and submit application
	
	CRITICAL: You MUST select embassy location BEFORE attempting captcha!
	CRITICAL: You MUST check all required checkboxes BEFORE trying to access lower fields!
	
	SAMPLE DATA TO USE:
	- Full Name: David Alexander Chen
	- Date of Birth: February 14, 1988
	- Place of Birth: San Francisco, CA, USA
	- Nationality: United States
	- Email: dchen.test@gmail.com
	- Phone: +1-555-234-5678
	- Address: 789 Pine Street, San Francisco, CA 94108
	- Purpose: Business Conference
	- Duration: 7 days
	- Employer: Digital Innovations Corp
	- Position: Senior Software Developer
	
	CAPTCHA SOLVING WITH QWEN2.5-VL VISION:
	- Use your exceptional vision capabilities for reading distorted captcha text
	- When you see a captcha image, analyze it very carefully:
	  * Read each character individually from left to right
	  * Pay attention to case sensitivity (uppercase/lowercase letters)
	  * Distinguish similar characters: 0 vs O, 1 vs I vs l, 5 vs S, 8 vs B, 6 vs G, 2 vs Z
	  * Handle wavy, rotated, crossed-out, or overlapping text
	  * Look for noise lines and ignore them
	- Enter the exact text you see in the captcha image
	- If captcha validation fails, refresh and carefully read the new image
	- You have exceptional vision capabilities for accurate captcha recognition
	
	FORM COMPLETION STRATEGY:
	- Fill forms systematically section by section
	- CRITICAL: Before moving to next section, verify ALL required fields in current section are completed
	- ALWAYS check for unchecked checkboxes, empty required fields, or unselected dropdowns
	- If you see checkboxes (like terms/conditions agreements), CHECK THEM FIRST before proceeding
	- Look for elements like "I agree", "I acknowledge", checkboxes that need to be selected
	- Required field validation: Ensure no red errors or missing field warnings before scrolling down
	- Select appropriate options from dropdowns
	- Handle date pickers and complex form elements
	- Save progress frequently to avoid data loss
	- Take screenshots at key milestones for verification
	- Be patient with page loading times and government website quirks
	- If fields become inaccessible, scroll back UP to find missing required elements
	
	INTELLIGENT SCROLLING STRATEGY:
	- SCROLL SLOWLY: Use scroll(direction="down", num_pages=0.3) for careful, controlled scrolling
	- STAY AWARE: After each scroll, carefully examine what became visible before taking action
	- METHODICAL APPROACH: Scroll small amounts (0.3 pages) to avoid missing important elements
	- Before looking for buttons like "Continue", "Next", "Submit" - always scroll down slowly first
	- Government forms often have content below the visible area - scroll incrementally to find it
	- If you can't find expected buttons/fields, use multiple small scroll actions to reveal content
	- Use scroll(direction="down", num_pages=0.3) instead of large scrolls or scroll_to_text
	- After filling a section, scroll down slowly to find the next section or continue button
	- If a form seems incomplete or you're stuck, try multiple small scrolls to see more options
	- DS160 forms are long - expect multiple sections requiring careful, slow scrolling
	- NEVER get stuck in loops - if scroll_to_text fails, use small scroll actions instead
	- If element index not found, it may mean prerequisite fields above need completion first
	- When fields are inaccessible, check if required fields above are properly filled
	
	EMBASSY SELECTION (STEP 1):
	- Choose any valid embassy from the dropdown list FIRST
	- Good options: "CANADA, TORONTO", "ENGLAND, LONDON", "GERMANY, BERLIN"
	- Select the embassy BEFORE trying to solve captcha
	- The captcha only appears/works AFTER embassy is selected
	"""
	
	try:
		# Create agent with Qwen2.5-VL for superior vision
		agent = Agent(
			task="Complete DS160 application: navigate → FIRST select embassy location → THEN solve captcha with vision → fill all sections → submit",
			llm=llm,
			use_vision=True,  # Enable Qwen2.5-VL vision for captcha solving
			extend_system_message=system_message,
			browser_profile=profile,
			save_conversation_path="optimal_qwen_vl_ds160_conversation.json"
		)
		
		# Custom error handler for learning
		class LearningErrorHandler:
			def __init__(self, learning_sys):
				self.learning_system = learning_sys
				self.successful_actions = []
				self.current_page_context = ""
			
			def record_success(self, action_type, element_index):
				self.successful_actions.append(f"{action_type}:{element_index}")
				if len(self.successful_actions) >= 3:  # Record sequences of 3+ actions
					self.learning_system.record_successful_sequence(self.successful_actions[-3:])
			
			def record_failure(self, element_index, error_msg):
				self.learning_system.record_failed_element(element_index, error_msg, self.current_page_context)
				print(f"📝 Learning: Recorded failure for element {element_index}: {error_msg[:50]}...")
			
			def update_page_context(self, context):
				self.current_page_context = context[:200]
		
		error_handler = LearningErrorHandler(learning_system)
		
		print("🌐 Starting optimized DS160 form filling...")
		print("🧠 Qwen2.5-VL handling both form logic and captcha solving")
		print("👁️ Using superior vision capabilities for accurate captcha recognition")
		print("⚡ Optimized for vision accuracy and speed")
		print("🎓 Learning system will track errors and improve over time")
		
		# Monkey-patch agent's run method to include learning
		original_run = agent.run
		
		async def run_with_learning(*args, **kwargs):
			try:
				# Run original agent
				result = await original_run(*args, **kwargs)
				
				# Analyze results for learning
				if hasattr(result, 'all_results'):
					for i, action_result in enumerate(result.all_results):
						if action_result.error:
							# Extract element index from error if possible
							error_msg = str(action_result.error)
							if "element index" in error_msg.lower():
								try:
									# Try to extract element index from error message
									import re
									match = re.search(r'element\s+index\s+(\d+)', error_msg.lower())
									if match:
										element_idx = int(match.group(1))
										error_handler.record_failure(element_idx, error_msg)
								except:
									pass
							
							# Check for dependency patterns
							if "not found in DOM" in error_msg:
								learning_system.record_dependency("prerequisite_field", "current_field", "DOM_dependency")
								print(f"🎓 Learning: Element not found - likely requires prerequisite completion above")
						else:
							# Record successful action
							if hasattr(action_result, 'extracted_content'):
								error_handler.update_page_context(str(action_result.extracted_content))
				
				return result
			except Exception as e:
				error_handler.record_failure(-1, str(e))
				raise
		
		# Replace run method with learning-enhanced version
		agent.run = run_with_learning
		
		# Run the complete DS160 workflow
		result = await agent.run(max_steps=50)  # Allow sufficient steps
		
		print("\n✅ DS160 form filling completed!")
		print(f"📊 Final result: {result}")
		
		# Show learning summary
		print("\n📚 Learning Summary:")
		print(f"   Failed patterns recorded: {len(learning_system.memory['failed_element_patterns'])}")
		print(f"   Successful sequences recorded: {len(learning_system.memory['successful_sequences'])}")
		print(f"   Dependencies discovered: {len(learning_system.memory['element_dependencies'])}")
		
		if result.is_done:
			print("🎉 Successfully completed DS160 application!")
			# Record overall success
			learning_system.record_successful_sequence(["navigation", "embassy_selection", "captcha_solving", "form_completion"])
		else:
			print("⚠️ Application incomplete - check conversation log")
		
	except Exception as e:
		print(f"❌ Error during DS160 form filling: {e}")
		learning_system.record_failed_element(-1, str(e), "general_exception")
		import traceback
		traceback.print_exc()

async def test_model_performance():
	"""
	Quick test of Qwen2.5-VL performance via OpenRouter
	"""
	print("\n🧪 Testing Qwen2.5-VL performance via OpenRouter...")
	
	import requests
	
	headers = {
		"Authorization": "Bearer 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",
		"Content-Type": "application/json"
	}
	
	payload = {
		"model": "qwen/qwen2.5-vl-32b-instruct",
		"messages": [
			{"role": "user", "content": "Hello! Are you ready to help with DS160 form filling and captcha solving with your superior vision capabilities?"}
		],
		"max_tokens": 100
	}
	
	try:
		response = requests.post(
			"https://openrouter.ai/api/v1/chat/completions",
			headers=headers,
			json=payload,
			timeout=10
		)
		
		if response.status_code == 200:
			result = response.json()
			print(f"✅ Qwen2.5-VL response: {result['choices'][0]['message']['content'][:150]}...")
		else:
			print(f"❌ API error: {response.status_code}")
	
	except Exception as e:
		print(f"❌ Connection error: {e}")

if __name__ == "__main__":
	# Test model first
	asyncio.run(test_model_performance())
	
	# Run the complete DS160 test
	asyncio.run(test_optimal_ds160())