{
  description = "Agent skills and configuration";

  outputs = { self }: {
    homeManagerModules.default = {
      home.file.".agents".source = self.outPath;
    };
  };
}
