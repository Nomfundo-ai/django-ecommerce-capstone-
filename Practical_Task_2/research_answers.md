# Practical Task 2 - Research Answers

*(Written independently, in my own words, as instructed - no material has
been copied or quoted from any source.)*

## 1. The Python `requests` module

`requests` is a third-party Python library that makes it much simpler to
send HTTP requests and work with their responses than using Python's
built-in `urllib` tools directly. Instead of manually building headers,
encoding query strings, and managing connections, a developer can call a
small set of straightforward functions - `requests.get()`,
`requests.post()`, `requests.put()`, `requests.delete()`, and so on - each
named after the HTTP method it performs.

A typical use looks like this:

```python
import requests

response = requests.get("https://api.example.com/products", params={"category": "shoes"})
if response.status_code == 200:
    data = response.json()
```

Under the hood, `requests` builds the raw HTTP request (method, URL,
headers, body), sends it over the network, and wraps the reply in a
`Response` object that exposes convenient attributes: `status_code` for the
HTTP status, `headers` for the response headers, `text` for the raw body as
a string, and `.json()` to automatically parse a JSON body into a Python
dictionary or list. It also handles things a developer would otherwise have
to do by hand, such as URL-encoding query parameters, following redirects,
managing cookies and sessions, setting a request timeout, attaching
authentication (basic auth, bearer tokens, etc.), and sending form data or
file uploads as a `POST` body. Because of this, `requests` is the library
most Python developers reach for whenever their code needs to call an
external web service or API, including the kind of RESTful APIs discussed
in question 3 below.

## 2. JSON and XML

Both JSON (JavaScript Object Notation) and XML (eXtensible Markup Language)
are text-based formats used to represent structured data so it can be
stored, transmitted between systems, and understood by different
programming languages. They are commonly used for API responses,
configuration files, and data interchange between a client and a server.

**JSON** represents data as nested objects (key-value pairs, written with
curly braces) and arrays (written with square brackets), closely resembling
how data structures look in many programming languages.

**XML** represents data as nested elements marked up with opening and
closing tags, similar in spirit to HTML, and can also attach attributes to
each element.

### JSON

**Advantages**
1. Lightweight and compact - fewer characters are needed to represent the
   same data compared to XML, which reduces payload size over a network.
2. Maps naturally onto native data structures (objects/dictionaries and
   arrays/lists) in most modern languages, including Python and
   JavaScript, so it needs very little translation once parsed.
3. Faster to parse in most implementations, partly because the format is
   simpler and there is no need to resolve tags, namespaces, or DTDs.
4. Human-readable and easy to write by hand for small payloads, making it
   pleasant to debug and to use for hand-written configuration.

**Disadvantages**
1. Has no built-in support for comments, which makes JSON awkward as a
   configuration-file format where explanatory notes are useful.
2. Has a smaller, less expressive type system than XML - for example, it
   has no native date/time type, so dates are usually encoded as plain
   strings and re-parsed by convention rather than by the format itself.
3. Does not support attributes on values or mixed content (text
   interspersed with markup) the way XML does, which can make certain
   document-like data awkward to represent.
4. Lacks a widely-adopted, built-in schema/validation standard as mature
   and universally supported as XML's DTD/XSD, so validating the shape of
   a JSON document usually relies on a separate, less standardised tool
   (such as JSON Schema).

### XML

**Advantages**
1. Has strong, mature support for schemas and validation (DTD, XSD),
   allowing the exact structure and data types of a document to be
   formally defined and automatically checked.
2. Supports comments, attributes, and namespaces, which make it well
   suited to representing complex, document-style, or hierarchical data
   with rich metadata.
3. Is a long-established, widely supported standard with mature tooling
   across almost every programming language and enterprise system,
   including many legacy systems still in production use.
4. Can represent mixed content (regular text combined with embedded
   markup), which is useful for document formats such as configuration
   files with descriptions, or markup-heavy content.

**Disadvantages**
1. Considerably more verbose than JSON - opening and closing tags, plus
   optional attributes, mean XML documents are usually much larger for the
   same underlying data.
2. Slower and more resource-intensive to parse, especially for large
   documents, because XML parsers must handle a more complex grammar
   (tags, attributes, namespaces, entities).
3. Less natural mapping onto native programming-language data structures,
   so working with parsed XML in code (e.g. via a DOM tree) is often more
   cumbersome than working with a JSON object.
4. Considered outdated for most modern web/API use cases; the ecosystem
   and tooling around JSON (especially for JavaScript-heavy web
   applications) has become the default, so XML is comparatively less
   convenient to use for new, lightweight API work.

## 3. RESTful APIs

REST (Representational State Transfer) is an architectural style for
designing networked applications, rather than a strict protocol. An API
that follows REST's conventions is described as "RESTful." A RESTful API
exposes **resources** - things such as products, users, or orders - each
identified by its own URL (e.g. `/products/42/`), and lets clients
interact with those resources using the standard HTTP methods: `GET` to
retrieve a resource, `POST` to create one, `PUT`/`PATCH` to update one, and
`DELETE` to remove one.

A core idea behind REST is **statelessness**: each request from a client to
a server must contain all the information the server needs to process it,
and the server does not store any session state about the client between
requests. Any state that needs to persist (such as "who is logged in") is
instead carried by the client on every request, typically via a token or
cookie. RESTful APIs typically exchange data using a format such as JSON
(discussed above), and responses generally include a standard HTTP status
code (e.g. `200 OK`, `201 Created`, `404 Not Found`) so that the outcome of
a request can be understood without inspecting the body.

**Advantages**
1. Statelessness makes RESTful APIs straightforward to scale horizontally,
   since any server instance can handle any request without needing to
   share session state with other instances.
2. Built directly on standard, universally supported HTTP methods and
   status codes, so almost any programming language or tool (including the
   `requests` module from question 1) can consume a RESTful API without
   needing a specialised client library.
3. Resources map cleanly to intuitive, predictable URLs, which makes a
   well-designed RESTful API easy for other developers to explore, reason
   about, and document.
4. Flexible about the data format used for the request/response body -
   although JSON is the most common choice today, a RESTful API is not
   tied to one specific format the way some other API styles are.

**Disadvantages**
1. Statelessness means every request must resend any context the server
   would otherwise "remember," which can add overhead (e.g. re-sending an
   authentication token on every call).
2. A fixed, resource-based structure can lead to **over-fetching** (getting
   more data in a response than the client actually needs) or
   **under-fetching** (needing several separate requests to gather related
   data), a pain point that alternative approaches such as GraphQL were
   designed to address.
3. There is no single official specification enforcing "REST" the way
   there is for something like SOAP, so different teams' RESTful APIs can
   vary quite a bit in style and consistency, making standardisation
   across an organisation harder.
4. Versioning a RESTful API as its resources evolve (e.g. adding new
   required fields) can be awkward, often requiring URL-based versions
   (`/v1/`, `/v2/`) or careful backward-compatible design to avoid breaking
   existing clients.
