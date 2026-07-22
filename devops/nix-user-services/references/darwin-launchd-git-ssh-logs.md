# Darwin LaunchAgents: Git SSH auth and useful logs

Use when a macOS Home Manager `launchd.agents` service runs a Git/libgit2-based tool but commits do not push, and Unified Logging shows only sparse macOS/network noise.

## Symptoms

- `launchctl print gui/$UID/<label>` shows the agent is `running` and `last exit code = (never exited)`.
- The repo is ahead of upstream, but the service did not push.
- Manual `git push --dry-run` succeeds from the interactive shell.
- `/usr/bin/log show --process <process>` contains little beyond system/network messages.
- Generated plist has `StandardOutPath = null` and `StandardErrorPath = null`.

## Checks

```bash
label=org.nix-community.home.git-watch-dotfiles
launchctl print gui/$UID/$label
ps eww -p <pid> -o command | tr ' ' '\n' | grep -E '^(HOME|SSH_AUTH_SOCK|PATH)='
SSH_AUTH_SOCK=<socket-from-service> ssh-add -l 2>&1 || true
SSH_AUTH_SOCK=$HOME/.1password/agent.sock ssh-add -l 2>&1 || true
git push --dry-run origin HEAD:master
```

If the service socket has no identities but `$HOME/.1password/agent.sock` does, the LaunchAgent is not using the interactive SSH agent. Git/libgit2 services may not honor OpenSSH `~/.ssh/config` `IdentityAgent`; pass `SSH_AUTH_SOCK` explicitly.

## Home Manager override pattern

```nix
launchd.agents.<agent-name>.config = lib.mkIf pkgs.stdenv.isDarwin {
  EnvironmentVariables = {
    SSH_AUTH_SOCK = "${config.home.homeDirectory}/.1password/agent.sock";
  };

  StandardOutPath = "${config.home.homeDirectory}/Library/Logs/<agent-name>.out.log";
  StandardErrorPath = "${config.home.homeDirectory}/Library/Logs/<agent-name>.err.log";
};
```

Then activate and restart:

```bash
darwin-rebuild switch --flake .
launchctl kickstart -k gui/$UID/<label>
tail -f ~/Library/Logs/<agent-name>.err.log
```

## Notes

- macOS Unified Logging is not a substitute for stdout/stderr capture from simple CLI LaunchAgents.
- Prefer explicit `EnvironmentVariables.SSH_AUTH_SOCK` for unattended Git services that use libgit2 or their own SSH callbacks.
- Some watch/commit tools only push after they create a new commit. If previous commits are already ahead, manually run `git push origin <branch>` once to unstick the repo, then verify the next service-created commit pushes.
