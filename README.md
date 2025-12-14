# Mosaic Project

Mosaic is a full-stack AI-powered interest analysis and content recommendation system. It allows users to upload images, URLs, or text, which are then analyzed by a suite of AI services to generate a personalized interest graph and recommend relevant content.

## Key Technologies

### Frontend
*   **Framework:** Next.js (v15) with React and TypeScript
*   **Styling:** Tailwind CSS
*   **Authentication:** Supabase Auth

### Backend
*   **Framework:** FastAPI with Python
*   **Database:** Supabase (PostgreSQL)
*   **File Storage:** Supabase Storage

### AI Services
*   **Visual Understanding:** DeepSeek-OCR
*   **Textual Inference:** DeepSeek-V3.2
*   **Web Content Conversion:** Jina Reader
*   **Search:** Tavily AI / Serper.dev

## Architecture

The application is structured as a monorepo with two main components:

*   `frontend/`: A Next.js application that serves as the user interface.
*   `backend/`: A FastAPI application that provides the core business logic, AI service integration, and database access.

Communication between the frontend and backend is handled via a RESTful API. User data and file uploads are stored in a Supabase PostgreSQL database and Supabase Storage, respectively.

## Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites

*   Python 3.12+
*   Node.js 18+
*   A Supabase account (or a local Supabase setup)

### 1. Database Setup

1.  **Supabase Project:** Log in to your [Supabase Dashboard](https://app.supabase.com/) and select or create a project.
2.  **SQL Editor:** Navigate to the "SQL Editor" section.
3.  **Schema:** Execute the SQL commands from `backend/database/schema.sql` to create the necessary tables.
4.  **Storage Bucket:** Ensure a storage bucket named `uploads` is created in your Supabase project (under the Storage section).

### 2. Backend Setup

1.  **Navigate to Backend:**
    ```bash
    cd backend
    ```
2.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Environment Variables:** Create a `.env` file in the `backend/` directory based on `backend/.env.example`. Fill in your Supabase credentials and API keys for the AI services (DeepSeek, Jina, Tavily AI, Serper.dev).

    Example `backend/.env`:
    ```
    SUPABASE_URL="YOUR_SUPABASE_URL"
    SUPABASE_ANON_KEY="YOUR_SUPABASE_ANON_KEY"
    SUPABASE_SERVICE_ROLE_KEY="YOUR_SUPABASE_SERVICE_ROLE_KEY"
    SUPABASE_DB_PASSWORD="YOUR_SUPABASE_DB_PASSWORD"
    DEEPSEEK_API_KEY="YOUR_DEEPSEEK_API_KEY"
    JINA_API_KEY="YOUR_JINA_API_KEY"
    TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
    SERPER_API_KEY="YOUR_SERPER_API_KEY"
    ```

5.  **Run Development Server:**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    The backend API will be available at `http://localhost:8000`. You can access the Swagger UI documentation at `http://localhost:8000/docs`.

### 3. Frontend Setup

1.  **Navigate to Frontend:**
    ```bash
    cd frontend
    ```
2.  **Install Dependencies:**
    ```bash
    npm install
    ```
3.  **Environment Variables:** Create a `.env.local` file in the `frontend/` directory based on `frontend/.env.local.example`. Configure your Supabase URL, anon key, and the backend API address.

    Example `frontend/.env.local`:
    ```
    NEXT_PUBLIC_SUPABASE_URL="YOUR_SUPABASE_URL"
    NEXT_PUBLIC_SUPABASE_ANON_KEY="YOUR_SUPABASE_ANON_KEY"
    NEXT_PUBLIC_BACKEND_URL="http://localhost:8000"
    ```

4.  **Run Development Server:**
    ```bash
    npm run dev
    ```
    The frontend application will be available at `http://localhost:3000`.

## Development Conventions

*   **Dependency Management:** Python dependencies are managed with `pip` and `requirements.txt`. Frontend dependencies are managed with `npm` and `package.json`.
*   **Code Style:** Adhere to the established coding styles within each respective part of the codebase (TypeScript for frontend, Python for backend).
*   **API:** The backend exposes a RESTful API for the frontend. API endpoints are documented in the main `README.md` (this file) and accessible via Swagger UI at `http://localhost:8000/docs`.
*   **Authentication:** User authentication is handled by Supabase Auth on the frontend.
*   **Environment Variables:** All sensitive information should be stored in `.env` files (e.g., `.env`, `.env.local`) and *not* committed to version control. The project is pre-configured with `.env.example` files to guide setup.

## Testing

*   **API Testing:** A `test-api.sh` script is provided at the project root for testing the backend API.

## Contributing

Contributions are welcome! Please fork the repository, create a new branch for your features or bug fixes, and submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.