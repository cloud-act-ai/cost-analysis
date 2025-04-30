-- Create LLM Model for GenAI Analysis
CREATE OR REPLACE MODEL `finops360-dev-2025.test.llm_model`
OPTIONS (
  model_type='REMOTE_MODEL',
  endpoint='https://us-central1-aiplatform.googleapis.com/v1/projects/finops360-dev-2025/locations/us-central1/publishers/google/models/gemini-pro'
);