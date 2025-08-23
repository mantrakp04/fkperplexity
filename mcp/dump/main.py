"""
Browser-Use Agent Flow Diagram
==============================

Based on analysis of https://github.com/browser-use/browser-use/tree/main

This diagram shows the core agent loop and flow, excluding peripheral components.
"""

# Agent Flow Diagram (ASCII representation)
agent_flow_diagram = """
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BROWSER-USE AGENT FLOW                                │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   USER TASK     │───▶│   AGENT INIT    │───▶│  TASK PARSING   │
│                 │    │                 │    │                 │
│ "Find repo      │    │ • LLM Setup     │    │ • Goal Analysis │
│  stars"         │    │ • Controller    │    │ • Plan Creation │
└─────────────────┘    │ • Browser       │    │ • Tool Selection│
                       │   Session       │    └─────────────────┘
                       └─────────────────┘              │
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  BROWSER SETUP  │    │  EXECUTION      │
                       │                 │    │  PLANNING       │
                       │ • Profile       │    │ • Action Steps  │
                       │ • Navigation    │    │ • Tool Mapping  │
                       │ • DOM Ready     │    │ • Priority      │
                       └─────────────────┘    │   Ordering      │
                                │             └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   DOM STATE     │    │  TOOL EXECUTION │
                       │   EXTRACTION    │    │                 │
                       │                 │    │ • Browser      │
                       │ • Page Snapshot│    │   Actions      │
                       │ • Element      │    │ • File System   │
                       │   Detection    │    │ • MCP Tools     │
                       │ • Accessibility│    │ • Custom Tools  │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  STATE ANALYSIS │    │  RESULT         │
                       │                 │    │  PROCESSING     │
                       │ • Current Page  │    │                 │
                       │ • Available     │    │ • Success/Fail  │
                       │   Elements      │    │ • Data          │
                       │ • Navigation    │    │   Extraction   │
                       │   History       │    │ • Error         │
                       └─────────────────┘    │   Handling      │
                                │             └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  LLM DECISION   │    │  NEXT ACTION    │
                       │                 │    │  DETERMINATION  │
                       │ • Context       │    │                 │
                       │   Analysis      │    │ • Continue      │
                       │ • Tool          │    │   Task?         │
                       │   Selection     │    │ • Task Complete?│
                       │ • Action        │    │ • Need More     │
                       │   Planning      │    │   Info?         │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  ACTION         │    │  TASK           │
                       │  EXECUTION      │    │  COMPLETION     │
                       │                 │    │                 │
                       │ • Browser       │    │ • Final         │
                       │   Navigation    │    │   Results       │
                       │ • Element       │    │ • Summary       │
                       │   Interaction   │    │ • Output        │
                       │ • Data          │    │   Generation    │
                       │   Collection    │    │ • Cleanup       │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  LOOP           │    │  EXIT           │
                       │  CONTINUATION   │    │                 │
                       │                 │    │ • Task Complete │
                       │ • Update State  │    │ • Results       │
                       │ • Next          │    │   Returned      │
                       │   Iteration     │    │ • Resources     │
                       │ • Continue      │    │   Cleaned       │
                       │   Until Done    │    │ • Session End   │
                       └─────────────────┘    └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CORE COMPONENTS                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

1. AGENT SERVICE (browser_use/agent/service.py)
   • Main orchestration logic
   • Task execution loop
   • LLM interaction management
   • State tracking

2. CONTROLLER (browser_use/controller/service.py)
   • Tool registry and execution
   • MCP server integration
   • Action dispatching
   • Result handling

3. BROWSER SESSION (browser_use/browser/session.py)
   • Playwright browser management
   • Page navigation
   • Event handling
   • Profile management

4. DOM SERVICE (browser_use/dom/service.py)
   • Page state extraction
   • Element detection
   • Accessibility information
   • DOM serialization

5. MESSAGE MANAGER (browser_use/agent/message_manager/service.py)
   • LLM communication
   • Context management
   • Memory handling
   • Response processing

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              KEY FLOW PATTERNS                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

• OBSERVE → THINK → ACT → OBSERVE (ReAct pattern)
• Continuous state monitoring and adaptation
• Tool selection based on current context
• Error recovery and retry mechanisms
• Parallel task execution where possible
• Memory persistence across iterations

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              INTEGRATION POINTS                                │
└─────────────────────────────────────────────────────────────────────────────────┘

• MCP (Model Context Protocol) servers
• External tool integrations
• Browser automation frameworks
• File system operations
• API interactions
• Custom tool development
"""

print(agent_flow_diagram)

# Additional detailed analysis
print("\n" + "="*80)
print("DETAILED COMPONENT ANALYSIS")
print("="*80)

print("""
1. AGENT INITIALIZATION FLOW:
   - Task parsing and goal setting
   - LLM model initialization
   - Controller setup with tool registry
   - Browser session creation
   - DOM service initialization

2. EXECUTION LOOP MECHANICS:
   - Continuous state observation
   - LLM decision making
   - Tool execution and result processing
   - State updates and context management
   - Loop continuation until task completion

3. TOOL EXECUTION FLOW:
   - Tool selection based on current context
   - Parameter validation and preparation
   - Execution with error handling
   - Result processing and state updates
   - Integration with next iteration

4. STATE MANAGEMENT:
   - DOM state persistence
   - Navigation history tracking
   - Tool execution history
   - Error state management
   - Memory and context persistence

5. ERROR HANDLING AND RECOVERY:
   - Tool execution failures
   - Browser navigation errors
   - LLM communication issues
   - State inconsistency recovery
   - Retry mechanisms with backoff
""")
