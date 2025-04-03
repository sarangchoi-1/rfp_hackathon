# RFP Pilot - AI-Powered RFP Generator

RFP Pilot is an automated system that generates Request for Proposal (RFP) documents using conversational AI. Leveraging RAG (Retrieval Augmented Generation) technology, it references relevant cases and best practices while creating customized RFPs through user interaction.

🌟 Key Features

- Project information collection through conversational interface
- Intelligent information retrieval and utilization based on RAG
- Real-time RFP outline generation
- Structured output in HTML format

🔧 System Architecture

```
허거덩거덩스/
├── agent/                 # AI agent related code
│   ├── core/             # Core agent logic
│   └── memory/           # Conversation memory management system
├── config/               # Environment configuration files
├── data/                 # Data processing and loading
│   └── dataloader.py     # Upstage API-based data loader
├── rag_pipeline/         # RAG pipeline implementation
├── streamlit_ui/         # Streamlit-based user interface
├── tests/                # Test code
└── utils/                # Utility functions
```

⚙️ Installation & Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
- Create `config/.env` file:
```env
OPENAI_API_KEY=your_openai_api_key
UPSTAGE_API_KEY=your_upstage_api_key
```

🚀 Running the Application

1. Launch Streamlit UI:
```bash
cd streamlit_ui
streamlit run app.py
```

2. Run main application:
```bash
python main.py
```

💻 Core Components

Agent Interface
- Conversation management and information extraction
- Project information analysis
- RFP outline generation coordination

RAG Pipeline
- Dual retrieval system implementation
- Related document and case search
- Response augmentation based on search results

Memory System
- Conversation context maintenance
- Information tracking and management
- Conversation state management

Data Loader
- ## Data loading using Upstage API
- Data preprocessing and refinement
- Search index construction

📝 Usage Example

1. Access web interface
2. Answer project-related questions
3. Review real-time generated RFP outline
4. Provide additional information as needed
5. Generate final RFP document

🔑 API Key Requirements

- OpenAI API key: For GPT-4 model usage
- Upstage API key: For data loading and processing

👥 How to Contribute

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
