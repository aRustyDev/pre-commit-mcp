# TODO

- Support HTTP based access
  - `npx -y mcp-remote https://mcp.example.com/`
  - Support passing `pre-commit-config` as json, with project_id
    - Storing and analzying config across projects.
    - Keep "lessons learned", "FAQ w/ answers", "anti-patterns", "patterns", etc
      - Lessons Learned: Deep explaination of the why
      - FAQ: Quick solution/debug patterns to keep development cycles fast
      - Patterns & Anti-Patterns: Assist in generative developement/design of new pre-commit-configs/hooks
    - Keep Hook library and metadata
      - Written in <Lang>
      - Author
      - Activity
    - Support backends like Kuzu, Falkor, Mongo etc
  - Support passing Hook output to this endpoint directly
    - Identify common issues, propose long-term solutions
