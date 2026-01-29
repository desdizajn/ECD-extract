public class CC529AInputDto
    {
        public HeaheaDto HEAHEA { get; set; }
        public Traexpex1Dto TRAEXPEX1 { get; set; }
        public Traconce1Dto TRACONCE1 { get; set; }
        public SeaInfSliDto SEAINFSLI { get; set; }
        public List<GooitegdsDto> GOOITEGDS { get; set; }
    }

    public class HeaheaDto
    {
        public decimal? TotGroMasHEA307 { get; set; }
        public string IdeOfMeaOfTraAtDHEA78 { get; set; }
        public string TraModAtBorHEA76 { get; set; }
        public string CouOfDisCodHEA55 { get; set; }
        public string CouOfDesCodHEA30 { get; set; }
        public object ConIndHEA96 { get; set; }
        public string DecPlaHEA394 { get; set; }
        public string NatOfMeaOfTraCroHEA87 { get; set; }
    }

    public class Traexpex1Dto
    {
        public string NamEX17 { get; set; }
        public string TINEX159 { get; set; }
        public string CitEX124 { get; set; }
        public string CouEX125 { get; set; }
        public string StrAndNumEX122 { get; set; }
        public string PosCodEX123 { get; set; }
    }

    public class Traconce1Dto
    {
        public string NamCE17 { get; set; }
        public string TINCE159 { get; set; }
        public string CitCE124 { get; set; }
        public string CouCE125 { get; set; }
        public string StrAndNumCE122 { get; set; }
        public string PosCodCE123 { get; set; }
    }

    public class SeaInfSliDto
    {
        public string SeaNumSLI2 { get; set; }
        public List<SeaIdSidDto> SEAIDSID { get; set; }
    }

    public class SeaIdSidDto
    {
        public string SeaIdeSID1 { get; set; }
    }

    public class GooitegdsDto
    {
        public string IteNumGDS7 { get; set; }
        public decimal? GroMasGDS46 { get; set; }
        public string GooDesGDS23 { get; set; }
        public string UNDanGooCodGDI1 { get; set; }

        public ComcodDto COMCODGODITM { get; set; }
        public List<Pacgs2Dto> PACGS2 { get; set; }
        public List<Prododc2Dto> PRODOCDC2 { get; set; }
    }

    public class ComcodDto
    {
        public string ComNomCMD1 { get; set; }
    }

    public class Pacgs2Dto
    {
        public string KinOfPacGS23 { get; set; }
        public string NumOfPacGS24 { get; set; }
        public string MarNumOfPacGS21 { get; set; }
    }

    public class Prododc2Dto
    {
        public string DocTypDC21 { get; set; }
        public string DocRefDC23 { get; set; }
    }