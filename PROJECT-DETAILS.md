# Issue Ticket

Companies raise tickets on their projects. Application staff assigned to a project update the work. Anyone assigned to that project can use its live chat. A person who is not assigned cannot find or join that room.

## Roles

Each account has one role.

| Role | Belongs to a company | What they do |
| --- | --- | --- |
| Super Admin | No | Creates and edits application admins and application users. Can change passwords. Can open every company, project, and ticket. |
| Application Admin | No | Creates a company and its company admins. Sees tickets that are not completed. Assigns application staff to projects. Can update any ticket's status. |
| Application User | No | Sees and updates tickets only on projects they are assigned to, including status. |
| Company Admin | Yes | Creates that company's projects and tickets. Creates company users and assigns them to projects. Cannot change ticket status. |
| Company User | Yes | On assigned projects: views tickets, creates tickets, adds notes and screenshots, and chats. Cannot create projects, users, or change status. |

Company Admin and Company User accounts must have a company. The three staff roles must not. Deactivate an account instead of deleting it. `createsuperuser` creates a Super Admin.

## Companies and projects

An Application Admin or Super Admin creates a company and its first Company Admin. More company admins can be added later. A new company admin is added to the company's existing projects.

A Company Admin or Super Admin creates projects. Every company admin of that company becomes a member of a new project.

Membership rules:

- A Company Admin adds and removes Company Users from the same company.
- An Application Admin or Super Admin adds and removes Application Users, Application Admins, and themselves.
- A company user cannot be placed on another company's project.
- Several people can be members of one project.

Membership is the permission to work a project's tickets and to enter its chat. Tickets are not assigned to one person.

## Tickets

A ticket belongs to one project and has a title, description, status, screenshots, and notes.

Statuses are Open, In progress, Waiting, Resolved, and Closed. Not completed means Open, In progress, or Waiting. Staff ticket lists default to not completed.

Who can create a ticket: Super Admin on any project, and Company Admin or Company User on a project they belong to.

Who can add notes and screenshots: anyone who can view the ticket. Notes and status changes share one thread that the company can see.

Who can change status: Super Admin, Application Admin, and an Application User who is a member of the project. A status change is recorded as a note.

Screenshots are jpg, png, gif, or webp images, up to 5 MB each.

## Chat

Each project has one room, created with the project. Messages are stored and delivered live with Django Channels. The connection is accepted only for an active member of that project. Application staff are not in the room unless they have been added as members.

With `REDIS_URL` empty, chat uses an in-memory channel layer for a single local process. A Redis URL shares messages across processes.

## Pages

- `/accounts/login/` sign in
- `/` home, with the role's recent tickets
- `/users/` Super Admin manages application staff. Company Admin manages company users.
- `/companies/` and `/companies/new/` companies and the first company admin
- `/projects/` and `/projects/<id>/` project details and member assignment
- `/projects/<id>/chat/` the project room
- `/tickets/` filter by project and status
- `/tickets/new/` and `/tickets/<id>/` create a ticket, then notes, screenshots, and status

Someone who is not allowed to open a page gets a refusal. A project or ticket outside their scope is not found.

## Templates

Pages live in one `templates/` folder, split into `accounts`, `users`, `companies`, `projects`, `tickets`, `chat`, and `partials`. Role checks stay in the views. The same ticket page hides the status control for company roles.
