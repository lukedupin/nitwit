# nitwit 

A disorganized and cumbersome ticketing system attempting to increase laborious tasks while obscuring priority or useful project insight.

***nitwit*** is a scatterbrained or incompetent person; the natural friend of a **git**, an unpleasant, incompetent, annoying, senile, or childish person.

## Concepts

> #ethos ^acknowledged @everyone

* Source code is a story. Tickets, ideas, bugs, and feature requests are an indistinguishable part of that story. 
* Commit messages without context into the ticketing system are largely useless.
* Ticket systems, hosted on a centralized website to facilitate a subscription pay model is a bad workflow.
* Ticketing history as it pertains to source code commits must be guaranteed.
* Ticketing should work completely offline.
* CLI first.
* Flat files in human readable format to facilitate any open source project.

> #integration ^completed @rlyman @dangerdave

nitwit is hopelessly integrated into git. .git/config is where the local nitwit configuration is help. nitwith only works inside of a git repo. Git hooks provide commit message integration.

> #simple ^testing @orby

* Just enough features.
* Focused on extremely quick actions. Most activities are completed in less than 10 seconds.
* Unopinionated

## Terms

1. **sprint** - A list of tickets a user is actively working on. A ticket is considered active if it appears on a sprint. A ticket that is ~~crossed out~~ denotes that it is no longer active, but is still listed on a sprint.
1. **user** - The "username" part of email address that is referenced in the commit log. 
1. **category** - A collection for tickets. Categories have properties which define how tickets are displayed. Categories create workflows:
    * Pending - A new ticket
    * Acknowledged - The ticket is accepted for work
    * Testing - QA testers
    * Completed - Hidden in most cases
    * Trash - A ticket that wont be completed
    * Carrot cake - ... Come up with your own workflow? Make it yours.
1. **tag** - Tags are used to group tickets. Tags can be used to:
    * Define logic program divisions
    * Group large code updates
    * Establish ticket types like: **bugs** or **features**
    * Filtering ticket visibility
1. **ticket** - An actionable item. Ticket properties include:
    * Description of a task. Pictures, tickets, bullet points
    * ~~Subitems provide a checkbox like format~~
    * One single category this ticket belongs to
    * Many tags
    * Many users
    * Notes - Added as progress continues
    * Active / Inactive state - Is this ticket on a sprint list?
    * A git log which shows what code changes occurred while this ticket was active.
    * Due date

## Interfacing with nitwit

**nw** - nw is the command line tool for interfacing with your ticketing system.

### init - Initialize your nitwit

```
cd <into existing git repo>
nw init
```

You'll notice a new folder now exists inside of your repo: nitwit. This is where all your **tickets**, **categories**, **tags** and **sprints** live.

### category - list, create, edit your ticket collections

```
# List out categories
nw category
Categories
    #trash
    #completed
    #testing
    #in_progress
    #pending

# Create a category
nw category phish
Created category #phish

# Edit a category
nw category phish
Created category #phish
```