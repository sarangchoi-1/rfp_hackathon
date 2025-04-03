import streamlit as st
import sys
import os
from datetime import datetime
import importlib.util
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))  # Adds the project root to Python path
from agent.memory.memory_system import MemorySystem

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the agent interface module
agent_interface_path = os.path.join(project_root, 'agent', 'core', 'agent_interface.py')
spec = importlib.util.spec_from_file_location("agent_interface", agent_interface_path)
agent_interface = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_interface)
AgentInterface = agent_interface.AgentInterface

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "project_info" not in st.session_state:
        st.session_state.project_info = {
            "project_name": None,
            "goal": None,
            "requirements": [],
            "constraints": [],
            "timeline": None,
            "budget": None,
            "stakeholders": [],
            "additional_context": []
        }
    if "last_outline" not in st.session_state:
        st.session_state.last_outline = None
    
    memory_system = MemorySystem()

    # Always reinitialize the agent to ensure we have the latest version
    st.session_state.agent = AgentInterface(memory_system)
    if "conversation_started" not in st.session_state:
        st.session_state.conversation_started = False

    # Add this to show when updates occur
    if "update_counter" not in st.session_state:
        st.session_state.update_counter = 0

def display_chat_message(message, is_user=False):
    """Display a chat message with the appropriate styling."""
    if isinstance(message, dict):
        # If message is a dictionary, extract the content
        content = message.get("content", "")
    else:
        # If message is a string, use it directly
        content = message
        
    with st.chat_message("user" if is_user else "assistant"):
        st.markdown(content)  # Use markdown instead of write for better formatting

def display_outline(result: str):
    """Display the generated outline in a structured format."""
    if isinstance(result, dict):
        content = result.get("outline", "")
    elif isinstance(result, str):
        content = result
    else:
        content = str(result)
        
    html_template = content.replace("```html", "").replace("```", "")
    st.html(html_template)

def update_project_info(response: str):
    """Update project info based on the response content and check if outline should update."""
    project_info = st.session_state.project_info
    
    # Add to context
    project_info["additional_context"].append(response)
    
    # Use the existing analyze_conversation method to extract information
    analysis = st.session_state.agent.analyze_conversation(
        project_info,
        st.session_state.messages
    )
    
    # Update project info with extracted information
    if analysis and "extracted_info" in analysis:
        extracted_info = analysis["extracted_info"]
        for key, value in extracted_info.items():
            if key in project_info and value:
                project_info[key] = value
        
        # If we got any new information, update the outline
        if extracted_info:
            try:
                result = st.session_state.agent.generate_outline(project_info)
                st.session_state.last_outline = result["outline"]  # Just store the result
                st.session_state.update_counter += 1  # Increment counter
            except Exception as e:
                st.error(f"개요 업데이트 중 오류 발생: {str(e)}")
    
    return analysis

def generate_outline_directly():
    """Generate outline directly without conversation."""
    with st.spinner("제안서 개요를 생성하는 중..."):
        try:
            result = st.session_state.agent.generate_outline(st.session_state.project_info)
            if isinstance(result, dict):
                outline = result.get("outline", "")
            else:
                outline = str(result)
            display_outline(outline)
            st.session_state.last_outline = outline
            st.session_state.outline_generated = True
        except Exception as e:
            st.error(f"개요 생성 중 오류 발생: {str(e)}")

def main():
    # Set page config
    st.set_page_config(
        page_title="RFP 아웃라인 작성 에이전트",
        page_icon="📝",
        layout="wide"
    )

    # Initialize session state
    initialize_session_state()

    # Add title and description
    st.title("🛫 RFP Pilot")
    st.markdown("""
    이 애플리케이션은 대화를 통해 프로젝트에 대한 정보를 수집하고, 
    맞춤형 제안서 개요를 생성해드립니다.
    """)

    # Create two columns for chat and outline
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("💬 대화")
        
        # Create a container for chat messages
        chat_container = st.container()
        
        # Create the input box at the bottom
        prompt = st.chat_input("여기에 메시지를 입력하세요...")
        
        # Display chat history inside the container
        with chat_container:
            # Display chat history
            for message in st.session_state.messages:
                display_chat_message(message["content"], message["is_user"])

            # Start conversation if not started
            if not st.session_state.conversation_started:
                initial_message = "안녕하세요! 저는 제안서 작성을 도와드리는 AI 어시스턴트입니다. 어떤 프로젝트를 준비하고 계신가요?"
                display_chat_message(initial_message)
                st.session_state.messages.append({"content": initial_message, "is_user": False})
                st.session_state.conversation_started = True

        # Handle user input
        if prompt:
            # Display user message
            with chat_container:
                display_chat_message(prompt, is_user=True)
            st.session_state.messages.append({"content": prompt, "is_user": True})

            # Update project info and get analysis
            analysis = update_project_info(prompt)
            
            # Generate next question
            if st.session_state.agent.should_continue_conversation(st.session_state.project_info):
                next_question = st.session_state.agent.generate_next_question(
                    st.session_state.project_info,
                    st.session_state.messages
                )
                display_chat_message(next_question)
                st.session_state.messages.append({"content": next_question, "is_user": False})
            
            # Only rerun if there's new extracted information
            if analysis and analysis.get("extracted_info"):
                st.rerun()

    with col2:
        st.subheader("📄 RFP 개요")
        
        # Create three columns in col2 to center the button
        left_spacer, center_col, right_spacer = st.columns([1, 2, 1])
        
        with center_col:
            if st.button("RFP 아웃라인 생성하기", type="primary", use_container_width=True):
                generate_outline_directly()

if __name__ == "__main__":
    main() 