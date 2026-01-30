# stratify

## Running Locally

Follow these steps to set up and run the project locally:

1. **Install dependencies**

   ```bash
   uv sync
   ```

2. **Activate your Python environment**

   ```bash
   # For virtualenv or venv
   source <your-env>/bin/activate
   ```

3. **Set up environment variables**
   - Add your Google API key and Firecrawl API key in the required `.env` files.
   - Refer to the `.env.example` files in each agent directory for the required variables and structure.

4. **Run the application**
   ```bash
   python app.py
   ```
