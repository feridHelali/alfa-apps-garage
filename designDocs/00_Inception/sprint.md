# Sprint: Inception

## Main Goal

Build a desktop Application with Python / PyQt / H2 Database Engine that manage "Garage de Reparation de Voiture".

## Todos

1- Scaffold the application using DDD/TDD/SOLID and take in consideration to build an installer (32bit/64bit) for windows.
2- Architect the System like old day Kernel (Domaine), Gui Layer, tools/utilities folder/lib, persistence layer...
3- Build Multi Document Applications (MDI)
4- Support i18n (fr/En) customable
5- add "Societe" management feature is kind of license and all relate info, logo,...
6- built in Report generator like old days (Crystal Report) for printing (invoices, reports...), that save format in json. 
7- build seed db for first use.
8- use Master/Detail forms pattern while there is One to Many relation ship between entities (and both if many to Many)
9- the system mast has authentication/RBAC feature or role based access (roles are superadmin, admin and technician)
10- the super admin has the ability to manage user, customize reports, self manage db snapshots

NB:
Break down this sprint as like, implement the stuff, update the sub-sprints and report all in md file enriched with SVG illustration for generating a user guide/ developer guide later
I have added event_storming.md as my first try with gemini to have insight on EventStorming (feel free to refactor/ add / enhance / abstract a way)
