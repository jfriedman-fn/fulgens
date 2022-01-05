# fulgens

## Setup

```bash
poetry install
```


## Usage

```python
import gitlab

PRIVATE_TOKEN = '<your private token>'

# Create gitlab object
gl = gitlab.Gitlab("https://gitlab.com", private_token=get_token())
gl.auth()

# Get all of the current user's groups
groups = gl.groups.list()

# Get all projects that the user is associated with by way of group membership
all_projects = []
for g in gl.groups.list():
    for p in g.projects.list():
        all_projects.append(gl.projects.get(p.get_id()))


# Get a project's open merge requests
my_project = gl.projects.get(project_id)
my_project.mergerequests.list(state="opened")
```

Note that I will librarize the existing code a bit in the future to abstract as much of the direct interaction with gitlab's library as is reasonable.
