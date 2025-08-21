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
          inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication defaultPoetryOverrides mkPoetryPackages;
          overrides = defaultPoetryOverrides.extend
                            (self: super: {
                              pagerduty = super.pagerduty.overridePythonAttrs
                              (
                                old: {
                                  buildInputs = (old.buildInputs or [ ]) ++ [ super.setuptools ];
                                }
                              );
                            });
          projectDir = ./.;
          preferWheels = true;
          # build the list of depnendencies from poetry lock file
          poetryPkgs = mkPoetryPackages {
            inherit projectDir preferWheels overrides;
          };
        in
        {
          packages = {
            cli = mkPoetryApplication {
                inherit projectDir preferWheels overrides;
                propagatedBuildInputs = [ poetryPkgs.poetryPackages ];
            };
            module = pkgs.python3Packages.buildPythonPackage {
                name = "pdh";
                src = self;
                projectDir = ./.;
                format = "pyproject";
                nativeBuildInputs = [
                  pkgs.python3Packages.poetry-core
                  pkgs.python3Packages.setuptools
                ];
                propagatedBuildInputs = [
                    poetryPkgs.poetryPackages
                    pkgs.python3Packages.setuptools
                ];
                nativeCheckInputs = [
                  pkgs.python3Packages.pytestCheckHook
                ];
                pythonImportsCheck = [
                  "pdh"
                ];
            };
            default = self.packages.${system}.cli;
          };

          devShell = pkgs.mkShell {
            inputsFrom = [ self.packages.${system}.cli];
            packages = with pkgs; [
              pre-commit
              go-task
              (python3.withPackages (ps: with ps; [ self.packages.${system}.module ]))
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
