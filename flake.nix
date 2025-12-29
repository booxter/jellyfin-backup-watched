{
  description = "Run Jellyfin backup utilities via Nix on any machine";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
      pythonEnv = pkgs: pkgs.python3.withPackages (ps: with ps; [ requests python-dotenv ]);
      mkApp = pkgs: script: pkgs.writeShellApplication {
        name = script;
        runtimeInputs = [ (pythonEnv pkgs) ];
        text = "exec ${pythonEnv pkgs}/bin/python ${./${script}.py} \"$@\"";
      };
    in {
      packages = forAllSystems (pkgs: {
        default = pythonEnv pkgs;
        copy-dates = mkApp pkgs "copy-dates";
        copy-userdata = mkApp pkgs "copy-userdata";
        backup-restore = mkApp pkgs "backup-restore";
      });

      apps = forAllSystems (pkgs:
        let
          pkgSet = self.packages.${pkgs.system};
          copyDates = { type = "app"; program = "${pkgSet.copy-dates}/bin/copy-dates"; };
          copyUserdata = { type = "app"; program = "${pkgSet.copy-userdata}/bin/copy-userdata"; };
          backupRestore = { type = "app"; program = "${pkgSet.backup-restore}/bin/backup-restore"; };
        in {
          default = copyDates;
          copy-dates = copyDates;
          copy-userdata = copyUserdata;
          backup-restore = backupRestore;
        });

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [ (pythonEnv pkgs) ];
        };
      });
    };
}
