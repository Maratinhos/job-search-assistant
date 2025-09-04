# Business Requirements Document (BRD): Job Search Assistant

**Version:** 1.0

**Date:** 2025-09-04

---

## 1.0 Introduction

### 1.1 Project Overview

The Job Search Assistant is a Telegram bot designed to help job seekers streamline and enhance their application process. The bot leverages Artificial Intelligence to analyze a user's resume against a specific job vacancy. Based on this analysis, it generates personalized content, including a cover letter and preparation plans for both HR and technical interviews. The system is designed to be interactive and user-friendly, guiding the user through each step of the process via a Telegram-based conversational interface.

### 1.2 Business Objectives

*   **Enhance Job Seeker Competitiveness:** Provide users with AI-powered tools to create high-quality, tailored job applications, thereby increasing their chances of securing interviews.
*   **Automate Repetitive Tasks:** Automate the creation of cover letters and interview preparation materials, saving users significant time and effort.
*   **Provide Actionable Insights:** Offer users a clear analysis of how their resume matches a vacancy, helping them understand their strengths and weaknesses for a particular role.
*   **Increase User Engagement:** Create a sticky and valuable service that users will return to throughout their job search.

### 1.3 Scope

#### In Scope:

*   User interaction via a Telegram bot interface.
*   User registration and profile management (implicitly through `chat_id`).
*   Uploading and storing of user resumes.
*   Saving and storing of job vacancies from user input.
*   AI-powered analysis to compare a single resume against a single vacancy.
*   Generation of a tailored cover letter.
*   Generation of a preparation plan for an HR interview screening call.
*   Generation of a preparation plan for a technical interview.
*   Logging of AI usage and associated costs for administrative purposes.
*   A survey mechanism to gather user feedback.

#### Out of Scope:

*   Direct integration with job boards for automatic vacancy searching (scraper for `hh.ru` exists but is not integrated into the main bot flow).
*   Management of multiple resumes or vacancies at the same time for a single analysis.
*   User accounts with login/password (authentication is based on Telegram `chat_id`).
*   A web-based interface.
*   Real-time job alerts or notifications.

---

## 2.0 Target Audience

The primary target audience for this project is **active job seekers**. This includes:

*   **Tech Professionals:** Software developers, data scientists, QA engineers, and other IT specialists looking for new opportunities.
*   **Recent Graduates:** University graduates entering the job market for the first time.
*   **Career Changers:** Professionals looking to transition into a new industry or role.

These users are typically comfortable with technology and are looking for tools to make their job search more efficient and effective.

---

## 3.0 Functional Requirements

### 3.1 User Onboarding and Management

*   **FR-001:** The system shall allow a new user to start interacting with the bot, triggering an onboarding sequence.
*   **FR-002:** The system shall uniquely identify each user by their Telegram `chat_id`.
*   **FR-003:** The system shall guide the user through the main menu options after the initial interaction.

### 3.2 Resume Management

*   **FR-004:** The system shall allow users to upload their resume as a file.
*   **FR-005:** The system shall store the user's resume for future use in analyses.
*   **FR-006:** The system shall allow a user to update or replace their existing resume.

### 3.3 Vacancy Management

*   **FR-007:** The system shall allow users to provide a job vacancy description.
*   **FR-008:** The system shall store the provided vacancy for use in an analysis.

### 3.4 AI-Powered Job Application Assistance

*   **FR-009:** The system shall allow a user to select one of their stored resumes and one of their stored vacancies to initiate an analysis.
*   **FR-010:** The system shall perform an AI-driven analysis of the resume against the vacancy to determine suitability.
*   **FR-011:** The system shall generate a tailored cover letter based on the resume and vacancy.
*   **FR-012:** The system shall generate a preparation plan for a potential HR screening call.
*   **FR-013:** The system shall generate a preparation plan for a potential technical interview.
*   **FR-014:** The system shall present the results of the analysis (cover letter, interview plans) to the user.

### 3.5 User Feedback

*   **FR-015:** The system shall be capable of presenting active surveys to users.
*   **FR-016:** The system shall record user responses to surveys.

---

## 4.0 Non-Functional Requirements

*   **NFR-001 (Usability):** The bot shall have a clear, intuitive, and conversational interface, with guided menus and clear instructions.
*   **NFR-002 (Performance):** AI analysis and content generation should be completed within a reasonable timeframe (e.g., under 60 seconds) to maintain user engagement.
*   **NFR-003 (Security):** User-uploaded documents (resumes) and personal data must be stored securely. The Telegram Bot Token and other secrets must be managed securely and not exposed in the codebase.
*   **NFR-004 (Reliability):** The bot shall be available and responsive 24/7. It should handle common errors gracefully and provide helpful feedback to the user.

---

## 5.0 Data Models

The system's functionality is supported by the following key data entities:

*   **User:** Represents a unique user of the bot.
*   **Resume:** Stores the file path and metadata for a user's resume.
*   **Vacancy:** Stores the text and metadata for a job vacancy.
*   **AnalysisResult:** Stores the output of the AI analysis, linking a specific resume to a specific vacancy. This includes the generated cover letter and interview plans.
*   **AIUsageLog:** Tracks AI API calls, token usage, and cost for monitoring and administrative purposes.
*   **Survey & SurveyAnswer:** Manages surveys and the collection of user feedback.

---

## 6.0 Assumptions and Constraints

*   **Assumption:** Users have a Telegram account and are familiar with using Telegram bots.
*   **Assumption:** Users will provide resumes and vacancy descriptions in a format and language that the AI model can process effectively.
*   **Constraint:** The quality and accuracy of the generated content are dependent on the underlying AI provider (e.g., OpenAI).
*   **Constraint:** The system requires a valid Telegram Bot Token and API keys for an AI service to be fully functional.
*   **Constraint:** The cost of operating the service is directly tied to the amount of AI usage by users.
