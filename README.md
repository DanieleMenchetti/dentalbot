# DentalBot
## Agentic AI Chatbot for dental offices


### Requirements
1. Node.js v24.15.0 LTS [link](https://nodejs.org/en/download)
2. Ollama [link](https://ollama.com/download)


### Backend
#### Setup
##### Keychain

<pre>
cd backend
</pre>

1. Create your keychain
<pre>
cp config/.keychain.example config/.keychain 
</pre>

##### Python
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

##### Ollama LLMs
1. Open a terminal and run Ollama. Keep this terminal always open to keep Ollama alive.
<pre>
ollama serve
</pre>

2. Open another terminal and get model qwen2.5 and mxbai-embed-large
<pre>
ollama pull qwen2.5
ollama pull mxbai-embed-large
</pre>

###### Google AI API
1. Get your [Google AI API](https://aistudio.google.com/api-keys)
2. Copy you API key into config/.keychain (GOOGLE_AI_API_KEY)

###### Google Calendar API
1. Follow the steps shown in paragraph "Google Cloud Setup" of this [page](https://github.com/nspady/google-calendar-mcp) to get a JSON file which contains your Google Calendar API key.  

2. Rename the JSON file in "gcp-oauth.keys.json" and place it under the folder "config"

3. Open another terminal and execute the commands below to authenticate yourself.
<pre>
# Linux
export GOOGLE_OAUTH_CREDENTIALS="./config/gcp-oauth.keys.json"

# Windows
$env:GOOGLE_OAUTH_CREDENTIALS="./config/gcp-oauth.keys.json"
</pre>
<pre>
npx @cocal/google-calendar-mcp auth
</pre>

4. Complete the authentication process.



#### Execution
Run backend
<pre>
uvicorn main:app --reload
</pre>


### Frontend
Open another terminal and run frontend
<pre>
cd frontend
npm install
npm run dev
</pre>