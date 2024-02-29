{
  description = "Nix: pdh";

  nixConfig.bash-prompt-prefix = "\(nix\)";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }@inputs:
    flake-utils.lib.eachSystem [
      "aarch64-darwin"
      "x86_64-darwin"
      "x86_64-linux"
    ]
      (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          devShell = pkgs.mkShell {
            buildInputs = [
              pkgs.pre-commit
              pkgs.go-task
              pkgs.python311
              pkgs.poetry
              pkgs.docker
            ];
            shellHook = ''
                task setup
                source .venv/bin/activate
                '';
          };
        }
      );
}
