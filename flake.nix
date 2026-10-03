{
  description = "Roy's agent skills and configuration";

  outputs = self: {
    homeManagerModules.default = {
      home.file.".agents".source = self.outPath;
    };
  };
}
