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
          override = defaultPoetryOverrides.extend
                            (self: super: {
                              pdpyras = super.pdpyras.overridePythonAttrs
                              (
                                old: {
                                  buildInputs = (old.buildInputs or [ ]) ++ [ super.setuptools ];
                                }
                              );
                            });
          poetryPkgs = mkPoetryPackages {
            projectDir = ./.;
            overrides = override;
            preferWheels = true;
          };
        in
        {
          packages = {
            cli = mkPoetryApplication {
                projectDir = ./.;
                overrides = override;
                preferWheels = true;
                propagatedBuildInputs = [ poetryPkgs.poetryPackages ];
            };
            module = pkgs.python3Packages.buildPythonPackage {
                name = "pdh";
                src = self;
                projectDir = ./.;
                format = "pyproject";
                nativeBuildInputs = [
                  pkgs.python3Packages.poetry-core
                ];
                propagatedBuildInputs = [
                    poetryPkgs.poetryPackages
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
            ];
            shellHook = ''
                '';
          };
        }
      );
}
