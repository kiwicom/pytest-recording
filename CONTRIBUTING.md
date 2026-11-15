# Contributing to pytest-recording

Welcome! We are very happy that you're reading this!

Your feedback and your experience are important for the project :)

## Feature requests and feedback

If you'd like to suggest a feature, feel free to [submit an issue](https://github.com/kiwicom/pytest-recording/issues)
and:

- Write a simple and descriptive title to identify your suggestion.
- Provide as many details as possible, explain your context and how the feature should work.
- Explain why this improvement would be useful.
- Keep the scope narrow. This will make it easier to implement.

## Report bugs

Report bugs for pytest-recording in the [issue tracker](https://github.com/kiwicom/pytest-recording/issues).

If you are reporting a bug, please:

- Write a simple and descriptive title to identify the problem.
- Describe the exact steps which reproduce the problem in as many details as possible.
- Describe the behavior you observed after following the steps and point out what exactly is the problem with that behavior.
- Explain which behavior you expected to see instead and why.
- Include Python / pytest-recording versions.

It would be awesome if you can submit a failing test that demonstrates the problem.

## Submitting Pull Requests

1. Fork the repository.

2. Install [prek](https://prek.j178.dev) hooks with `uvx prek install` to ensure style-guides and code checks are followed.

3. Target the `master` branch.

4. Follow **PEP 8** for naming and [ruff](https://github.com/astral-sh/ruff) for formatting.

5. Tests are run using `tox`:

   ```bash
   tox -e py314
   ```

   The test environments above are usually enough to cover most cases locally.

6. Write an entry to [CHANGELOG.md](https://github.com/kiwicom/pytest-recording/blob/master/CHANGELOG.md) under the matching section (`Added`, `Changed`, `Fixed`, `Removed`, `Documentation`).

7. Format your commit message according to the Conventional Commits [specification](https://www.conventionalcommits.org/en/).

If you have troubles with installing `pycurl` with `tox`, you could try to pass `CPPFLAGS` and `LDFLAGS`
with the `tox` command:

```bash
CPPFLAGS="-I/usr/local/opt/openssl/include" LDFLAGS="-L/usr/local/opt/openssl/lib" tox -p all
```

For each pull request, we aim to review it as soon as possible.
If you wait a few days without a reply, please feel free to ping the thread by adding a new comment.

At present the core developers are:

- Dmitry Dygalo ([@Stranger6667](https://github.com/Stranger6667))

Thanks!
