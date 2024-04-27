# Financial Management System

## Description

This Python web application provides comprehensive financial management functionalities, focusing on robust account handling, journal entries, and email notification systems. It's built using Django and designed to facilitate the management of financial records, user authentication, and dynamic data interaction.

### Key Features:

- **User Management**: Includes custom user models extending Django's built-in `AbstractUser` for handling user information, including security questions, password expiry, and more.
- **Chart of Accounts (CoA)**: Manages financial accounts with functionalities to add, modify, deactivate, and reactivate accounts within the system, ensuring detailed tracking and auditing through event logs.
- **Journal Entries**: Facilitates the creation and management of journal entries, allowing users to add, approve, or reject entries based on detailed financial logic and audit requirements.
- **Email Notifications**: Implements an extensive email system that sends notifications upon various events, such as user registration, password resets, and journal entry updates, ensuring stakeholders are always informed.
- **Dynamic Financial Ratios**: Calculates and displays financial ratios in real-time, offering insights into the financial health of the business.
- **Security and Data Integrity**: Employs Django forms and custom validation methods to secure user data and ensure the integrity of the financial information processed through the system.

This application is intended for businesses needing a reliable and scalable solution to manage their financial records with high degrees of automation and security.

## Getting Started

### Dependencies

List any prerequisites, libraries, OS version, or tools that are required before installing the project.

- Python 3.8+
- Django 3.2+
- Other dependencies listed in `requirements.txt`

### Running the Application
1. Install python [link](https://www.python.org/downloads/) (make sure during installation you add to PATH.)
2. Check Python version in terminal ```python --version``` (if nothing shows up you need to check your python installation and make sure it was done correctly.)
3. Install Pip ```py get-pip.py```
4. Check Pip version in terminal ```pip --version``` (if nothing shows up you need to check your pip installation and make sure it was done correctly.)
4. CD into your the project Example: ```C:\Users\username\Documents\GitHub\Ledger-Logic```
5. Install the requirements.txt file ```pip install requirements.txt```
6. Create a ```.env``` file in the Root of the project and paste the following variable name ```DATABASE_URL=postgres://``` you will need to get the key from one of the project owners.
7. CD back into your project folder and type the following command ```python manage.py runserver``` then paste the generated URL into your browser.

