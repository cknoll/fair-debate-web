# Development Documentation

## Use Cases

This part of the documentation is targeted towards the development team. It documents the details of the usage mechanics.



### Basic Use Case (with multiple users)


:::{attention}
This section is yet only a placeholder.
:::

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
