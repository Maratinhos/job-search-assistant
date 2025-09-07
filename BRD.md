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
*   Uploading and storing of user resumes, including parsing from `hh.ru` URLs.
*   Saving and storing of job vacancies from user input, including parsing from `hh.ru` URLs.
*   AI-powered analysis to compare a single resume against a single vacancy.
*   Generation of a tailored cover letter.
*   Generation of a preparation plan for an HR interview screening call.
*   Generation of a preparation plan for a technical interview.
*   A survey mechanism to gather user feedback.
*   A points-based billing system for monetizing AI features.
*   Tracking of user acquisition channels via UTM sources.
*   Logging of AI usage and associated costs for administrative purposes.

#### Out of Scope:

*   Direct integration with job boards for automatic vacancy searching beyond `hh.ru`.
*   Management of multiple resumes or vacancies at the same time for a single analysis.
*   User accounts with login/password (authentication is based on Telegram `chat_id`).
*   A web-based interface.
*   Real-time job alerts or notifications.
*   A live, integrated payment provider (payment flow is currently emulated).

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

*   **FR-001:** A new user can start interacting with the bot, which triggers an onboarding sequence.
*   **FR-002:** The system uniquely identifies each user by their Telegram `chat_id`.
*   **FR-003:** If the user starts the bot via a referral link with a UTM source, the system shall record this source.
*   **FR-004:** The system guides the user through the main menu options after the initial interaction.

### 3.2 Resume Management

*   **FR-005:** The system shall allow users to upload their resume as a file or provide a URL from `hh.ru`.
*   **FR-006:** The system shall parse the resume from the provided file or URL and store its content.
*   **FR-007:** The system shall allow a user to update or replace their existing resume.

### 3.3 Vacancy Management

*   **FR-008:** The system shall allow users to provide a job vacancy description as text or a URL from `hh.ru`.
*   **FR-009:** The system shall parse the vacancy from the provided text or URL and store its content.

### 3.4 AI-Powered Job Application Assistance

*   **FR-010:** The system shall allow a user to select one of their stored resumes and one of their stored vacancies to initiate an analysis.
*   **FR-011:** The system shall perform an AI-driven analysis of the resume against the vacancy to determine suitability.
*   **FR-012:** The system shall generate a tailored cover letter based on the resume and vacancy.
*   **FR-013:** The system shall generate a preparation plan for a potential HR screening call.
*   **FR-014:** The system shall generate a preparation plan for a potential technical interview.
*   **FR-015:** The system shall present the results of the analysis (cover letter, interview plans) to the user.

### 3.5 User Feedback

*   **FR-016:** The system shall be capable of presenting active surveys to users.
*   **FR-017:** The system shall record user responses to surveys.

### 3.6 Monetization and Billing

*   **FR-018:** The system shall allow a user to check their current points balance.
*   **FR-019:** The system shall allow a user to view available point packages for purchase.
*   **FR-020:** The system shall allow a user to select and purchase a point package (emulated).
*   **FR-021:** The system shall update the user's balance after a successful purchase.

---

## 4.0 Monetization

The service is monetized through a points-based system. Users spend points to access advanced AI-powered features. This allows for flexible usage and aligns costs with consumption.

*   **Points System:** Core AI actions, such as generating a cover letter or a full analysis, deduct a predetermined number of points from the user's balance.
*   **Checking Balance:** Users can check their current points balance at any time using the `/balance` command.
*   **Purchasing Points:** Users can purchase additional points using the `/buy` command. This command displays available packages of points at different price tiers.
*   **Payment Emulation:** The current implementation does not feature a live payment gateway. The purchase flow is emulated, meaning that upon selecting a package, the user's balance is credited with the points immediately without actual payment processing. This is intended for development and testing purposes.

---

## 5.0 Non-Functional Requirements

*   **NFR-001 (Usability):** The bot shall have a clear, intuitive, and conversational interface, with guided menus and clear instructions.
*   **NFR-002 (Performance):** AI analysis and content generation should be completed within a reasonable timeframe (e.g., under 60 seconds) to maintain user engagement.
*   **NFR-003 (Security):** User-uploaded documents (resumes) and personal data must be stored securely. The Telegram Bot Token and other secrets must be managed securely and not exposed in the codebase.
*   **NFR-004 (Reliability):** The bot shall be available and responsive 24/7. It should handle common errors gracefully and provide helpful feedback to the user.

---

## 6.0 Data Models

The system's functionality is supported by the following key data entities:

*   **User:** Represents a unique user of the bot.
*   **Resume:** Stores the file path and metadata for a user's resume.
*   **Vacancy:** Stores the text and metadata for a job vacancy.
*   **AnalysisResult:** Stores the output of the AI analysis, linking a specific resume to a specific vacancy. This includes the generated cover letter and interview plans.
*   **AIUsageLog:** Tracks AI API calls, token usage, and cost for monitoring and administrative purposes.
*   **Survey & SurveyAnswer:** Manages surveys and the collection of user feedback.
*   **UserBalance:** Stores the current points balance for each user.
*   **Transaction:** Records all transactions, including point purchases (deposits) and feature usage (withdrawals).
*   **UTMTrack:** Logs the UTM source for users who start the bot via a referral link, for marketing and analytics purposes.

---

## 7.0 Assumptions and Constraints

*   **Assumption:** Users have a Telegram account and are familiar with using Telegram bots.
*   **Assumption:** Users will provide resumes and vacancy descriptions in a format and language that the AI model can process effectively.
*   **Constraint:** The quality and accuracy of the generated content are dependent on the underlying AI provider (e.g., OpenAI).
*   **Constraint:** The system requires a valid Telegram Bot Token and API keys for an AI service to be fully functional.
*   **Constraint:** The cost of operating the service is directly tied to the amount of AI usage by users.
