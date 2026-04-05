# DentalBot
## Agentic AI Chatbot for dental offices

### Execution
1. Create virtualenv:
<pre>
python -m venv venv
</pre>

2. Activate it:
<pre>
#Linux
source venv/bin/activate

#Windows
.\venv\Scripts\activate
</pre>

3. Install requirements.txt:
<pre>
pip install -r requirements.txt
</pre>

4. Install [Ollama](https://ollama.com/download)

5. Open a terminal and run Ollama. Keep this terminal always open to keep Ollama alive.
<pre>
ollama serve
</pre>

6. Open another terminal and get model qwen2.5 and mxbai-embed-large
<pre>
ollama pull qwen2.5
ollama pull mxbai-embed-large
</pre>

7. Run main
<pre>
python main.py
</pre>