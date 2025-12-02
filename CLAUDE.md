# Instructions for Claude Code to build the moneybags web application
This file contains instructions for Claude Code to guide the building of the Moneybags web application.

# Purpose of the Moneybags web application
The purpose of the Moneybags web application is to help users to have control of their personal economty. The program will let users create yearly budgets (both for income and expenses), and then let uses register actual income and expenses as time passes by. The user should be able to attach comments to each value entered. The application should at least have four main parts: 1. Visually appealing dashbaord with interesting information, 2. Analysis where the user can deep dive into the data and query different things and drill. 3. Yearly budget (income and expensese) and yearly actual income and expenses (budget and actual income and expenses is in the same part). 4. Configuration options (where user can select Currency notation, and other typical user preferences)

The program needs to take into account that each year would have some of the same posts, which obviously need to be seen in relation to each other. But new posts may also exist, that has not been used in previous years. And posts that were used at some time, may no longer be used in future years. Ensuring data integrity, and the ability to analyse and see data across years is paramount.

Its an important thing here that the UX need to be supergood and smooth. This means that we need to make use of htmx for example, so saving and reloading happens automatically, withouth the user being redirected to the top of the page or in other ways loose context. 

# Tech stack
- The web application should be responsive design, so it also works on mobile phones, as well as on desktop
- FastAPI should be used for the backend
- Bootstrap with htmx should be used for the frontend. We should use a combination of base templates, partial templates and other templates
- Vanilla js should be used whenever js is needed. All js should be placed in the same js file, not placed inline in different html pages
- All CSS should be place in the same css file and referenced throughout the app
- TomSelect should be used for advanced input boxes, and if thats not needed use standard bootstrap and html input boxes
- Date and time picker should use Tempus Domino js library
- MariaDB should be used as the database. The program must support configuring this database connection.
- PeeWee ORM should be used to interact with the Mariadb database

# Architectural constraints
## General constraints
- main.py contains the router and should contain no business logic
- business_logic.py contains all business logic, calculations etc. Whenever CRUD operations are needed in the database, methods should always call database_manager.py and use the methods defined there. CRUD operations shall never be called directly from the business_logic module
- database_manager.py contains all methods necessary to do CRUD operations in the database
- database_model.py contains the model for the sqlite database
- The uvicorn_log_config.ini contains the logging configuration. All logging, both from fastapi and python, should be done in a uniform manner and logged to the docker container.
- utils.py contains helper methods, such as method to create UUIDs and other stuff that has the characteristics of being helper method
- The app should be able to run both locally when testing and developing, as well as being deployed as a docker container. See Gas Gauge, Gear Calc and Wheel Builder (all one folder up) for what patterns to use for logging and docker container deploy

## Database configuration
- The database configuration itself should be kept as simple as possible. Do not use backrefs or automatically generated IDs. Instead, always create uniue ids for records in the backend and submit that to the database. See 