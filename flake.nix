{
  description = "Nix: pdh";

  nixConfig.bash-prompt-prefix = "\(nix\)";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachSystem [
      "aarch64-darwin"
      "x86_64-darwin"
      "x86_64-linux"
    ]
      (system:
        let
          pkgs = import nixpkgs { inherit system; };

          # name, version and executable are derived from pyproject.toml
          pyproject = builtins.fromTOML (builtins.readFile ./pyproject.toml);
          pname = pyproject.project.name;
          exe = builtins.head (builtins.attrNames pyproject.tool.poetry.scripts);

          # sources plus poetry.lock, consumed by poetry at install time
          project = pkgs.stdenvNoCC.mkDerivation {
            inherit pname;
            inherit (pyproject.project) version;
            src = self;
            dontBuild = true;
            installPhase = ''
              mkdir -p $out/share/${pname}
              cp -r pyproject.toml poetry.lock README.md src $out/share/${pname}/
            '';
          };

          # the first run creates a per-version venv from poetry.lock
          cli = pkgs.writeShellScriptBin exe ''
            set -euo pipefail
            venv="''${XDG_CACHE_HOME:-$HOME/.cache}/${pname}/$(basename ${project})"
            if [ ! -x "$venv/bin/${exe}" ]; then
              trap 'rm -rf "$venv"' ERR
              ${pkgs.python3}/bin/python -m venv "$venv"
              VIRTUAL_ENV="$venv" PATH="$venv/bin:$PATH" \
                ${pkgs.poetry}/bin/poetry install --only main --no-interaction \
                --directory ${project}/share/${pname} >&2
              trap - ERR
            fi
            exec "$venv/bin/${exe}" "$@"
          '';
        in
        {
          packages = {
            inherit project cli;
            default = cli;
          };

          devShell = pkgs.mkShell {
            packages = with pkgs; [
              hadolint
              pre-commit
              go-task
              python3
              poetry
              docker
              cachix
              statix
            ];
            shellHook = ''
                '';
          };
        }
      );
}
