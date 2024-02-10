# Poster

## Motivation

Services of Monash Automation is built on top of an OPC UA server,
which records IoT sensor data and reacts to user inputs.

* sync version is deprecated, update with `asyncua` is required
* support more types (IP address, URL, emails...)
* hard to transform data between a Python object and OPC UA nodes
* boilerplate code for reading/updating nodes
* duplicated validation logic
* editor support (inline error prompt, type inference)

Currently team members are raw node operations using `asyncua`,
this significantly increases learning cost,
code is error-prone and is hard to update for new features.
Field validation code is duplicated

* read and write data in OOP methods
* no need to manage node id or browse path
