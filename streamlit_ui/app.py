import streamlit as st
import sys
import os
from datetime import datetime
import importlib.util

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
    # Always reinitialize the agent to ensure we have the latest version
    st.session_state.agent = AgentInterface()
    if "conversation_started" not in st.session_state:
        st.session_state.conversation_started = False
    if "outline_generated" not in st.session_state:
        st.session_state.outline_generated = False

def display_chat_message(message, is_user=False):
    """Display a chat message with the appropriate styling."""
    with st.chat_message("user" if is_user else "assistant"):
        st.markdown(message)

def display_outline(result: str):
    """Display the generated outline in a structured format."""
    html_template = result.replace("```html", "").replace("```", "")
    st.html(html_template)

def update_project_info(response: str):
    """Update project info based on the response content."""
    project_info = st.session_state.project_info
    project_info["additional_context"].append(response)

def generate_outline_directly():
    """Generate outline directly without conversation."""
    with st.spinner("제안서 개요를 생성하는 중..."):
        result = st.session_state.agent.generate_outline(st.session_state.project_info)
        print(result, "result!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
        display_outline(result["outline"])
        st.session_state.outline_generated = True

def main():
    # Set page config
    st.set_page_config(
        page_title="대화형 RFP Outline 생성기",
        page_icon="📝",
        layout="wide"
    )

    # Initialize session state
    initialize_session_state()

    # Add title and description
    st.title("💬 RFP 아웃라인 생성기")
    st.markdown("""
    이 애플리케이션은 대화를 통해 프로젝트에 대한 정보를 수집하고, 
    맞춤형 제안서 개요를 생성해드립니다. 자연스러운 대화를 통해 
    프로젝트에 대해 이야기를 나누어 보세요.
    """)

    # Add direct outline generation button
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("RFP 아웃라인 생성하기", type="primary"):
            
            generate_outline_directly()

    with col1:
        # Display chat history
        for message in st.session_state.messages:
            display_chat_message(message["content"], message["is_user"])

        # Start conversation if not started
        if not st.session_state.conversation_started:
            initial_message = "안녕하세요! 저는 제안서 작성을 도와드리는 AI 어시스턴트입니다. 어떤 프로젝트를 준비하고 계신가요?"
            display_chat_message(initial_message)
            st.session_state.messages.append({"content": initial_message, "is_user": False})
            st.session_state.conversation_started = True

        # Chat input
        if prompt := st.chat_input("여기에 메시지를 입력하세요..."):
            # Display user message
            display_chat_message(prompt, is_user=True)
            st.session_state.messages.append({"content": prompt, "is_user": True})

            # Update project info
            update_project_info(prompt)

            # Check if we should continue gathering information
            if st.session_state.agent.should_continue_conversation(st.session_state.project_info):
                # Generate next question
                next_question = st.session_state.agent.generate_next_question(
                    st.session_state.project_info,
                    st.session_state.messages
                )
                
                # Display agent's response
                display_chat_message(next_question)
                st.session_state.messages.append({"content": next_question, "is_user": False})
            else:
                # We have all required information, generate outline
                with st.spinner("제안서 개요를 생성하는 중..."):
                    print(st.session_state.project_info)
                    result = st.session_state.agent.generate_outline(st.session_state.project_info)
                    display_outline(result)
                    st.session_state.outline_generated = True
                
                # Ask if user wants to continue
                continue_msg = "제안서 개요가 생성되었습니다. 더 자세한 정보를 추가하시겠어요?"
                display_chat_message(continue_msg)
                st.session_state.messages.append({"content": continue_msg, "is_user": False})

        # Rerun to update the UI
            st.rerun()

if __name__ == "__main__":
    main() 