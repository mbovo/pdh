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
          inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication defaultPoetryOverrides;
          override = defaultPoetryOverrides.extend
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
          packages = {
             pdh = mkPoetryApplication {
                projectDir = ./.;
                overrides = override;
                preferWheels = true;
            };
            default = self.packages.${system}.pdh;
          };

          devShell = pkgs.mkShell {
            inputsFrom = [ self.packages.${system}.pdh];
            packages = with pkgs; [
              pre-commit
              go-task
              python311
              poetry
              docker
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
