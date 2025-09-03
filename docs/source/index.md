# fair-debate-web documentation

Add your content using **Markdown** syntax. See the
[Markdown Guide](https://www.markdownguide.org/) for details.

```{toctree}
:maxdepth: 2
:caption: Contents:
```

Hello world

```{uml}

:User: --> (Use)
"Group of\nAdministrators " as Admin
"Using the\napplication" as (Use)
Admin --> (Administering\nthe Application)
```



## Basic Use Case (with multiple users)

```{uml}

left to right direction
skinparam packageStyle rectangle

actor "User A" as UserA
actor "User B" as UserB
actor "User C" as UserC
actor "User D" as UserD

rectangle "Message Interaction System" {
  (Publish Message) as Publish
  (Answer Message) as Answer
  (Approve Third Party Answers) as Approve
}

UserA --> Publish: "Publishes message M1"
UserB --> Answer: "Can answer M1\n(normal status)"
UserC --> Answer: "Can answer M1\n(inofficial third party answers)"
UserD --> Answer: "Can answer M1\n(inofficial third party answers)"
UserB --> Approve: "Can approve\nthird party answers"

```