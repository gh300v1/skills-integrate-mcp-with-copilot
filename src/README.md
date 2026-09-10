# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Create a student account with a school association
- Log in and view a student profile
- Verify an email address for organization actions
- Sign up for activities using the logged-in student's identity

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/register`                                                  | Create a student account and session                               |
| POST   | `/auth/login`                                                     | Log in and create a session                                         |
| POST   | `/auth/logout`                                                    | End the current session                                             |
| GET    | `/auth/me`                                                        | Get the logged-in student's profile                                 |
| POST   | `/auth/verify-email`                                              | Verify the logged-in student's email                                |
| POST   | `/activities/{activity_name}/signup`                              | Sign up the logged-in student for an activity                       |
| DELETE | `/activities/{activity_name}/unregister`                          | Unregister the logged-in student                                   |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses normalized email as identifier:
   - Full name
   - Grade level
   - School, derived from the email domain
   - Password hash
   - Email verification state

All data, including users and sessions, is stored in memory, which means it will be reset when the server restarts. The registration response includes a verification token for this local exercise; a production deployment should deliver that token through an email provider instead.
