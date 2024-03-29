{
  description = "Nix: pdh";

  nixConfig.bash-prompt-prefix = "\(nix\)";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix, ... }@inputs:
    flake-utils.lib.eachSystem [
      "aarch64-darwin"
      "x86_64-darwin"
      "x86_64-linux"
    ]
      (system:
        let
          pkgs = import nixpkgs { inherit system; };
          p2nix = import poetry2nix { inherit pkgs; };
          override = p2nix.defaultPoetryOverrides.extend
                            (self: super: {
                              pdpyras = super.pdpyras.overridePythonAttrs
                              (
                                old: {
                                  buildInputs = (old.buildInputs or [ ]) ++ [ super.setuptools ];
                                }
                              );
                            });
        in
        {
          packages.default = p2nix.mkPoetryApplication {
            projectDir = ./.;
            overrides = override;
            preferWheels = true;
          };
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
                poetry install
                '';
          };
        }
      );
}
