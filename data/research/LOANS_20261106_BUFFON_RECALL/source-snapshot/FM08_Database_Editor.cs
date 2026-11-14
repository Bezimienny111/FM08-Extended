using System.Linq;

using System;

using System.Collections.Generic;

using System.ComponentModel;

using System.Diagnostics;

using System.Drawing;

using System.Globalization;

using System.IO;

using System.IO.Compression;

using System.Reflection;

using System.Runtime.CompilerServices;

using System.Runtime.InteropServices;

using System.Text;

using System.Windows.Forms;

using System.Xml;


[assembly: RuntimeCompatibility(WrapNonExceptionThrows = true)]

[assembly: CompilationRelaxations(8)]

[assembly: AssemblyVersion("0.0.0.0")]

public class FM08_Database_Editor : Form

{

	public class PersonDetails

	{
		public int UniqueId;

		public int PersonOffset;



		public int CA;



		public int PA;



		public int CurrentReputation;



		public int HomeReputation;



		public int WorldReputation;



		public int Height;



		public int Weight;



		public int ClubId;



		public string FirstName;



		public string LastName;



		public string CommonName;



		public DateTime? BirthDate;



		public int Age;



		public int NationId;



		public DateTime? ContractExpires;



		public int FirstNameIdOffset;



		public int LastNameIdOffset;



		public int CommonNameIdOffset;



		public int BirthDateOffset;



		public int ContractExpiresOffset;

		public int WeeklyWage;

		public byte SquadNumber;


		public int ClubIdOffset;



		public int NationIdOffset;

	}



	public class PlayerRecord

	{

		public int Id { get; set; }



		public string FirstName { get; set; }



		public string LastName { get; set; }



		public string CommonName { get; set; }



		public string Position { get; set; }



		public int Age { get; set; }



		public DateTime? BirthDate { get; set; }



		public string Nationality { get; set; }



		public string Club { get; set; }



		public int CA { get; set; }



		public int PA { get; set; }



		public int CurrentReputation { get; set; }



		public int HomeReputation { get; set; }



		public int WorldReputation { get; set; }



		public int Height { get; set; }



		public int Weight { get; set; }



		public DateTime? ContractExpires { get; set; }



		public int FirstNameIdOffset { get; set; }



		public int LastNameIdOffset { get; set; }



		public int CommonNameIdOffset { get; set; }



		public int BirthDateOffset { get; set; }



		public int ContractExpiresOffset { get; set; }



		public int ClubIdOffset { get; set; }



		public int NationIdOffset { get; set; }



		public int ClubId { get; set; }

		public bool ClubAssignmentPending { get; set; }

		public bool ContractExpiresPending { get; set; }

		public bool ContractDetailsPending { get; set; }



		public int NationId { get; set; }



		public DateTime? RetirementDate { get; set; }

		internal PlayerRecord NativeWriteCopy()
		{
			return (PlayerRecord)MemberwiseClone();
		}



		public List<string> Languages { get; set; }



		public List<string> Injuries { get; set; }



		public List<string> Bans { get; set; }



		public List<string> FavouriteClubs { get; set; }



		public List<string> DislikedClubs { get; set; }



		public List<string> FavouriteStaff { get; set; }



		public List<string> DislikedStaff { get; set; }



		public byte LeftFoot { get; set; }



		public byte RightFoot { get; set; }



		public byte Crossing { get; set; }



		public byte Dribbling { get; set; }



		public byte Finishing { get; set; }



		public byte Heading { get; set; }



		public byte LongShots { get; set; }



		public byte Marking { get; set; }



		public byte Movement { get; set; }



		public byte Passing { get; set; }



		public byte Penalties { get; set; }



		public byte Tackling { get; set; }



		public byte Creativity { get; set; }



		public byte FirstTouch { get; set; }



		public byte Technique { get; set; }



		public byte Corners { get; set; }



		public byte LongThrows { get; set; }



		public byte FreeKicks { get; set; }



		public byte Versatility { get; set; }



		// International Caps & Goals

		public byte InternationalApps { get; set; }

		public byte InternationalGoals { get; set; }

		public byte U21Apps { get; set; }

		public byte U21Goals { get; set; }



		// Person Data Attributes (Personality)

		public byte Adaptability { get; set; }

		public byte Ambition { get; set; }

		public byte Controversy { get; set; }

		public byte Determination { get; set; }

		public byte Loyalty { get; set; }

		public byte Pressure { get; set; }

		public byte Professionalism { get; set; }

		public byte Sportsmanship { get; set; }

		public byte Temperament { get; set; }



		// Job Preferences

		public byte JobPrefAssistantManager { get; set; }

		public byte JobPrefCoach { get; set; }

		public byte JobPrefFitnessCoach { get; set; }

		public byte JobPrefGoalkeepingCoach { get; set; }

		public byte JobPrefManager { get; set; }

		public byte JobPrefPhysio { get; set; }

		public byte JobPrefScout { get; set; }



		// Contract details

		public int WeeklyWage { get; set; }

		public byte SquadNumber { get; set; }



		// Preferred Moves (PPM)

		public List<string> PreferredMoves { get; set; }



		public byte Aggression { get; set; }



		public byte Anticipation { get; set; }



		public byte Bravery { get; set; }



		public byte Composure { get; set; }



		public byte Concentration { get; set; }



		public byte Consistency { get; set; }



		public byte Decisions { get; set; }



		public byte Dirtiness { get; set; }



		public byte Flair { get; set; }



		public byte ImportantMatches { get; set; }



		public byte Leadership { get; set; }



		public byte Positioning { get; set; }



		public byte Teamwork { get; set; }



		public byte WorkRate { get; set; }



		public byte Acceleration { get; set; }



		public byte Agility { get; set; }



		public byte Balance { get; set; }



		public byte InjuryProneness { get; set; }



		public byte Jumping { get; set; }



		public byte NaturalFitness { get; set; }



		public byte Pace { get; set; }



		public byte Stamina { get; set; }



		public byte Strength { get; set; }



		public int T89Offset { get; set; }



		public int PersonOffset { get; set; }



		public bool IsModified { get; set; }



		public byte AerialAbility { get; set; }



		public byte CommandOfArea { get; set; }



		public byte Communication { get; set; }



		public byte Eccentricity { get; set; }



		public byte Handling { get; set; }



		public byte Kicking { get; set; }



		public byte OneOnOnes { get; set; }



		public byte Reflexes { get; set; }



		public byte RushingOut { get; set; }



		public byte Throwing { get; set; }



		public byte TendencyToPunch { get; set; }



		public byte PosGK { get; set; }



		public byte PosSW { get; set; }



		public byte PosDL { get; set; }



		public byte PosDC { get; set; }



		public byte PosDR { get; set; }



		public byte PosDM { get; set; }



		public byte PosWBL { get; set; }



		public byte PosWBR { get; set; }



		public byte PosML { get; set; }



		public byte PosMC { get; set; }



		public byte PosMR { get; set; }



		public byte PosAML { get; set; }



		public byte PosAMC { get; set; }



		public byte PosAMR { get; set; }



		public byte PosST { get; set; }



		public byte FreeRole { get; set; }



		public string FullName

		{

			get

			{

				if (string.IsNullOrEmpty(FirstName))

				{

					return LastName;

				}

				return FirstName + " " + LastName;

			}

		}



		public string BirthDateStr

		{

			get

			{

				return BirthDate.HasValue ? BirthDate.Value.ToString("dd.MM.yyyy") : "-";

			}

		}



		public string ContractStr

		{

			get

			{

				return ContractExpires.HasValue ? ContractExpires.Value.ToString("dd.MM.yyyy") : "Brak (wolny agent)";

			}

		}



		public string HeightStr

		{

			get

			{

				return (Height > 0) ? (Height + " cm") : "-";

			}

		}



		public string WeightStr

		{

			get

			{

				return (Weight > 0) ? (Weight + " kg") : "-";

			}

		}



		public string ReputationStr

		{

			get

			{

				if (CurrentReputation == 0 && HomeReputation == 0 && WorldReputation == 0)

				{

					return "-";

				}

				return string.Format("{0} / {1} / {2}", CurrentReputation, HomeReputation, WorldReputation);

			}

		}



		public string PreferredFootStr

		{

			get

			{

				if (LeftFoot == 0 && RightFoot == 0)

				{

					return "-";

				}

				if (LeftFoot >= 15 && RightFoot >= 15)

				{

					return "Obie nogi (" + LeftFoot + "/" + RightFoot + ")";

				}

				if (LeftFoot > RightFoot)

				{

					return "Lewa (" + LeftFoot + "/" + RightFoot + ")";

				}

				if (RightFoot > LeftFoot)

				{

					return "Prawa (" + RightFoot + "/" + LeftFoot + ")";

				}

				return (LeftFoot > 0) ? ("Lewa (" + LeftFoot + ")") : ("Prawa (" + RightFoot + ")");

			}

		}

	}



	public class LoadDbResult

	{

		public List<PlayerRecord> Players;



		public byte[] PeopleDb;



		public byte[] PeopleDbHeader;



		public byte[] ServerDb;



		public byte[] ServerDbHeader;



		public string DbDir;



		public Dictionary<int, string> Clubs;



		public Dictionary<int, string> Nations;

	}



	public class CsvField

	{

		public string Key { get; set; }



		public string HeaderName { get; set; }



		public string[] Aliases { get; set; }



		public Func<PlayerRecord, string> Getter { get; set; }



		public Action<PlayerRecord, byte[], string> Setter { get; set; }

	}



	private ComboBox cbDatabases;



	private TextBox txtCustomPath;



	private Button btnBrowse;



	private Button btnLoad;



	private ProgressBar progressBar;



	private Label lblStatus;



	private TextBox txtSearch;



	private ComboBox cbClubFilter;



	private Button btnResetClub;



	private Label lblFoundCount;



	private DataGridView gridPlayers;



	private StatusStrip statusStrip;



	private ToolStripStatusLabel statusPlayerDetails;



	private bool sortAscending = true;



	private string lastSortColumn = "";



	private Label lblDetailFullName;



	private Label lblDetailSubInfo;



	private Label lblDetailMetaInfo;



	private Label lblDetailRepInfo;



	private Label valCrossing;



	private Label valDribbling;



	private Label valFinishing;



	private Label valHeading;



	private Label valLongShots;



	private Label valMarking;



	private Label valMovement;



	private Label valPassing;



	private Label valPenalties;



	private Label valTackling;



	private Label valCreativity;



	private Label valFirstTouch;



	private Label valTechnique;



	private Label valCorners;



	private Label valLongThrows;



	private Label valFreeKicks;



	private Label valVersatility;



	private Label valAggression;



	private Label valAnticipation;



	private Label valBravery;



	private Label valComposure;



	private Label valConcentration;



	private Label valConsistency;



	private Label valDecisions;



	private Label valDirtiness;



	private Label valFlair;



	private Label valImportantMatches;



	private Label valLeadership;



	private Label valPositioning;



	private Label valTeamwork;



	private Label valWorkRate;



	private Label valAcceleration;



	private Label valAgility;



	private Label valBalance;



	private Label valInjuryProneness;



	private Label valJumping;



	private Label valNaturalFitness;



	private Label valPace;



	private Label valStamina;



	private Label valStrength;



	private Label valLeftFoot;



	private Label valRightFoot;



	private Label valAerialAbility;



	private Label valCommandOfArea;



	private Label valCommunication;



	private Label valEccentricity;



	private Label valHandling;



	private Label valKicking;



	private Label valOneOnOnes;



	private Label valReflexes;



	private Label valRushingOut;



	private Label valThrowing;



	private Label valTendencyToPunch;



	private Label valPosGK;



	private Label valPosSW;



	private Label valPosDL;



	private Label valPosDC;



	private Label valPosDR;



	private Label valPosDM;



	private Label valPosWBL;



	private Label valPosWBR;



	private Label valPosML;



	private Label valPosMC;



	private Label valPosMR;



	private Label valPosAML;



	private Label valPosAMC;



	private Label valPosAMR;



	private Label valPosST;



	private Label valFreeRole;



	private Label valHiddenConsistency;



	private Label valHiddenImpMatches;



	private Label valHiddenDirtiness;



	private Label valHiddenVersatility;



	private Label valHiddenInjury;



	private static Font fontRegular = new Font("Segoe UI", 9f, FontStyle.Regular);



	private static Font fontBold = new Font("Segoe UI", 9f, FontStyle.Bold);



	private static Font fontTitle = new Font("Segoe UI", 12f, FontStyle.Bold);



	private static Font fontSection = new Font("Segoe UI", 9.5f, FontStyle.Bold);



	private List<PlayerRecord> allPlayers = new List<PlayerRecord>();



	private List<PlayerRecord> filteredPlayers = new List<PlayerRecord>();



	private BackgroundWorker loaderWorker;



	private byte[] loadedPeopleDbRaw;



	private byte[] loadedPeopleDbOrigHeader;



	private byte[] loadedServerDbRaw;



	private byte[] loadedServerDbOrigHeader;
	private byte[] loadedClientDbRaw;
	private byte[] loadedClientDbOrigHeader;



	private string loadedDbPath;



	private bool hasUnsavedChanges = false;



	public static Dictionary<int, string> LoadedClubs = new Dictionary<int, string>();



	public static Dictionary<int, string> LoadedNations = new Dictionary<int, string>();



	public static List<PlayerRecord> LoadedAllPlayers = new List<PlayerRecord>();



	public static Dictionary<string, int> FirstNamesRev = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);



	public static Dictionary<string, int> SurnamesRev = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);



	public static Dictionary<int, string> FirstNamesDict = new Dictionary<int, string>();



	public static Dictionary<int, string> SurnamesDict = new Dictionary<int, string>();



	public static Dictionary<int, int> SrvNameOffsetsByPid = new Dictionary<int, int>();



	public static Dictionary<string, int> ClubsRev = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);



	public static Dictionary<string, int> NationsRev = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);



	public static Dictionary<string, int> CommonNamesRev = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);



	private Button btnExportCsv;



	private Button btnImportCsv;



	private Button btnSaveDb;



	private Button btnEditPlayer;

	private Button btnAddPlayer;



	private MenuStrip mainMenu;



	public static List<CsvField> allCsvFields = new List<CsvField>();



	public static Dictionary<string, CsvField> csvFieldsByName = new Dictionary<string, CsvField>(StringComparer.OrdinalIgnoreCase);



	public FM08_Database_Editor()

	{

		InitCsvRegistry();

		InitializeComponent();

		DetectDatabases();

	}



	private void InitializeComponent()

	{

		this.Text = "Football Manager 2008 - Przeglądarka i Edytor Bazy Danych";

		base.Size = new System.Drawing.Size(1360, 850);

		this.MinimumSize = new System.Drawing.Size(1100, 650);

		base.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;

		this.Font = new System.Drawing.Font("Segoe UI", 9f, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point);

		this.BackColor = System.Drawing.Color.FromArgb(245, 247, 250);

		System.Windows.Forms.Panel panel = new System.Windows.Forms.Panel();

		panel.Dock = System.Windows.Forms.DockStyle.Top;

		panel.Height = 110;

		panel.BackColor = System.Drawing.Color.FromArgb(235, 240, 246);

		panel.Padding = new System.Windows.Forms.Padding(15, 10, 15, 10);

		System.Windows.Forms.Panel panel2 = panel;

		System.Windows.Forms.Label label = new System.Windows.Forms.Label();

		label.Text = "Wybierz bazę danych FM 2008:";

		label.Location = new System.Drawing.Point(15, 15);

		label.AutoSize = true;

		label.Font = new System.Drawing.Font("Segoe UI", 9f, System.Drawing.FontStyle.Bold);

		System.Windows.Forms.Label value = label;

		this.cbDatabases = new System.Windows.Forms.ComboBox

		{

			Location = new System.Drawing.Point(15, 38),

			Width = 320,

			DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList

		};

		this.cbDatabases.SelectedIndexChanged += new System.EventHandler(this.cbDatabases_SelectedIndexChanged);

		this.txtCustomPath = new System.Windows.Forms.TextBox

		{

			Location = new System.Drawing.Point(345, 38),

			Width = 430

		};

		this.btnBrowse = new System.Windows.Forms.Button

		{

			Text = "Przeglądaj...",

			Location = new System.Drawing.Point(785, 36),

			Width = 100,

			Height = 27,

			BackColor = System.Drawing.Color.White,

			FlatStyle = System.Windows.Forms.FlatStyle.System

		};

		this.btnBrowse.Click += new System.EventHandler(this.btnBrowse_Click);

		this.btnLoad = new System.Windows.Forms.Button

		{

			Text = "Wczytaj bazę",

			Location = new System.Drawing.Point(895, 35),

			Width = 130,

			Height = 29,

			BackColor = System.Drawing.Color.FromArgb(0, 122, 204),

			ForeColor = System.Drawing.Color.Black,

			Font = new System.Drawing.Font("Segoe UI", 9f, System.Drawing.FontStyle.Bold),

			FlatStyle = System.Windows.Forms.FlatStyle.System

		};

		this.btnLoad.Click += new System.EventHandler(this.btnLoad_Click);

		this.progressBar = new System.Windows.Forms.ProgressBar

		{

			Location = new System.Drawing.Point(15, 75),

			Width = 868,

			Height = 18,

			Visible = false

		};

		this.lblStatus = new System.Windows.Forms.Label

		{

			Location = new System.Drawing.Point(15, 76),

			Width = 868,

			Height = 20,

			Text = "Wybierz bazę danych i kliknij 'Wczytaj bazę'.",

			ForeColor = System.Drawing.Color.FromArgb(80, 80, 80)

		};

		panel2.Controls.Add(value);

		panel2.Controls.Add(this.cbDatabases);

		panel2.Controls.Add(this.txtCustomPath);

		panel2.Controls.Add(this.btnBrowse);

		this.btnSaveDb = new System.Windows.Forms.Button

		{

			Text = "Zapisz bazę...",

			Location = new System.Drawing.Point(1035, 35),

			Width = 110,

			Height = 29,

			BackColor = System.Drawing.Color.FromArgb(220, 240, 220),

			Font = new System.Drawing.Font("Segoe UI", 9f, System.Drawing.FontStyle.Bold),

			FlatStyle = System.Windows.Forms.FlatStyle.System,

			Enabled = false

		};

		this.btnSaveDb.Click += (object s, System.EventArgs e) =>

		{

			this.SaveDatabaseAs();

		};

		this.btnExportCsv = new System.Windows.Forms.Button

		{

			Text = "Eksport CSV",

			Location = new System.Drawing.Point(1155, 35),

			Width = 100,

			Height = 29,

			BackColor = System.Drawing.Color.White,

			FlatStyle = System.Windows.Forms.FlatStyle.System,

			Enabled = false

		};

		this.btnExportCsv.Click += (object s, System.EventArgs e) =>

		{

			this.ExportToCsv((this.filteredPlayers != null && this.filteredPlayers.Count > 0) ? this.filteredPlayers : this.allPlayers);

		};

		this.btnImportCsv = new System.Windows.Forms.Button

		{

			Text = "Import CSV",

			Location = new System.Drawing.Point(1265, 35),

			Width = 100,

			Height = 29,

			BackColor = System.Drawing.Color.White,

			FlatStyle = System.Windows.Forms.FlatStyle.System,

			Enabled = false

		};

		this.btnImportCsv.Click += (object s, System.EventArgs e) =>

		{

			this.ImportFromCsv();

		};

		panel2.Controls.Add(this.btnLoad);

		panel2.Controls.Add(this.btnSaveDb);

		panel2.Controls.Add(this.btnExportCsv);

		panel2.Controls.Add(this.btnImportCsv);

		panel2.Controls.Add(this.progressBar);

		panel2.Controls.Add(this.lblStatus);

		System.Windows.Forms.Panel panel3 = new System.Windows.Forms.Panel();

		panel3.Dock = System.Windows.Forms.DockStyle.Top;

		panel3.Height = 55;

		panel3.BackColor = System.Drawing.Color.White;

		panel3.Padding = new System.Windows.Forms.Padding(15, 10, 15, 10);

		System.Windows.Forms.Panel panel4 = panel3;

		System.Windows.Forms.Label label2 = new System.Windows.Forms.Label();

		label2.Text = "Szukaj zawodnika:";

		label2.Location = new System.Drawing.Point(15, 17);

		label2.AutoSize = true;

		label2.Font = new System.Drawing.Font("Segoe UI", 9f, System.Drawing.FontStyle.Bold);

		System.Windows.Forms.Label value2 = label2;

		this.txtSearch = new System.Windows.Forms.TextBox

		{

			Location = new System.Drawing.Point(135, 14),

			Width = 190,

			Font = new System.Drawing.Font("Segoe UI", 9.5f)

		};

		this.txtSearch.TextChanged += new System.EventHandler(this.txtSearch_TextChanged);

		System.Windows.Forms.Label label3 = new System.Windows.Forms.Label();

		label3.Text = "Klub:";

		label3.Location = new System.Drawing.Point(340, 17);

		label3.AutoSize = true;

		label3.Font = new System.Drawing.Font("Segoe UI", 9f, System.Drawing.FontStyle.Bold);

		System.Windows.Forms.Label value3 = label3;

		this.cbClubFilter = new System.Windows.Forms.ComboBox

		{

			Location = new System.Drawing.Point(380, 14),

			Width = 270,

			DropDownWidth = 360,

			MaxDropDownItems = 20,

			Font = new System.Drawing.Font("Segoe UI", 9.5f),

			AutoCompleteMode = System.Windows.Forms.AutoCompleteMode.SuggestAppend,

			AutoCompleteSource = System.Windows.Forms.AutoCompleteSource.ListItems,

			Enabled = false

		};

		this.cbClubFilter.Items.Add("-- Wczytaj bazę danych --");

		this.cbClubFilter.SelectedIndex = 0;

		this.cbClubFilter.SelectedIndexChanged += new System.EventHandler(this.cbClubFilter_SelectedIndexChanged);

		this.cbClubFilter.KeyDown += new System.Windows.Forms.KeyEventHandler(this.cbClubFilter_KeyDown);

		this.btnResetClub = new System.Windows.Forms.Button

		{

			Text = "Wyczyść",

			Location = new System.Drawing.Point(658, 13),

			Width = 65,

			Height = 27,

			Font = new System.Drawing.Font("Segoe UI", 8.5f),

			FlatStyle = System.Windows.Forms.FlatStyle.System,

			Enabled = false

		};

		this.btnResetClub.Click += new System.EventHandler(this.btnResetClub_Click);

		this.btnAddPlayer = new System.Windows.Forms.Button

		{

			Text = "+ Dodaj zawodnika",

			Location = new System.Drawing.Point(735, 13),

			Width = 145,

			Height = 27,

			Font = new System.Drawing.Font("Segoe UI", 8.5f, System.Drawing.FontStyle.Bold),

			BackColor = System.Drawing.Color.FromArgb(235, 250, 235),

			FlatStyle = System.Windows.Forms.FlatStyle.System,

			Enabled = false

		};

		this.btnAddPlayer.Click += (object s, System.EventArgs e) => this.AddNewPlayer();

		this.lblFoundCount = new System.Windows.Forms.Label

		{

			Location = new System.Drawing.Point(895, 17),

			AutoSize = true,

			Text = "Wczytaj bazę danych, aby wyszukać zawodników.",

			ForeColor = System.Drawing.Color.FromArgb(80, 80, 80)

		};

		panel4.Controls.Add(value2);

		panel4.Controls.Add(this.txtSearch);

		panel4.Controls.Add(value3);

		panel4.Controls.Add(this.cbClubFilter);

		panel4.Controls.Add(this.btnResetClub);

		panel4.Controls.Add(this.btnAddPlayer);

		panel4.Controls.Add(this.lblFoundCount);

		System.Windows.Forms.SplitContainer mainSplit = new System.Windows.Forms.SplitContainer

		{

			Dock = System.Windows.Forms.DockStyle.Fill,

			Orientation = System.Windows.Forms.Orientation.Horizontal,

			SplitterWidth = 6,

			BackColor = System.Drawing.Color.FromArgb(215, 225, 235)

		};

		base.Shown += (object s, System.EventArgs e) =>

		{

			try

			{

				if (mainSplit.Height > 550)

				{

					mainSplit.SplitterDistance = 280;

				}

			}

			catch

			{

			}

		};

		this.gridPlayers = new System.Windows.Forms.DataGridView

		{

			Dock = System.Windows.Forms.DockStyle.Fill,

			ReadOnly = true,

			AllowUserToAddRows = false,

			AllowUserToDeleteRows = false,

			SelectionMode = System.Windows.Forms.DataGridViewSelectionMode.FullRowSelect,

			MultiSelect = false,

			AutoGenerateColumns = false,

			BackgroundColor = System.Drawing.Color.White,

			BorderStyle = System.Windows.Forms.BorderStyle.None,

			RowHeadersVisible = false,

			EnableHeadersVisualStyles = false

		};

		this.gridPlayers.ColumnHeadersDefaultCellStyle.BackColor = System.Drawing.Color.FromArgb(230, 235, 242);

		this.gridPlayers.ColumnHeadersDefaultCellStyle.Font = new System.Drawing.Font("Segoe UI", 9f, System.Drawing.FontStyle.Bold);

		this.gridPlayers.ColumnHeadersHeight = 30;

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "Id",

			HeaderText = "ID",

			Width = 70

		});

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "FirstName",

			HeaderText = "Imię",

			Width = 110

		});

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "LastName",

			HeaderText = "Nazwisko / Przydomek",

			Width = 160

		});

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "Position",

			HeaderText = "Pozycja",

			Width = 100,

			Visible = true

		});

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "Age",

			HeaderText = "Wiek",

			Width = 50

		});

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "BirthDateStr",

			HeaderText = "Data ur.",

			Width = 80

		});

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "Nationality",

			HeaderText = "Narodowość",

			Width = 110

		});

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "Club",

			HeaderText = "Klub",

			Width = 160

		});

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "CA",

			HeaderText = "CA",

			Width = 50

		});

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "PA",

			HeaderText = "PA",

			Width = 50

		});

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "HeightStr",

			HeaderText = "Wzrost",

			Width = 65

		});

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "WeightStr",

			HeaderText = "Waga",

			Width = 65

		});

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "PreferredFootStr",

			HeaderText = "Noga",

			Width = 110

		});

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "ReputationStr",

			HeaderText = "Reputacja",

			Width = 110

		});

		this.gridPlayers.Columns.Add(new System.Windows.Forms.DataGridViewTextBoxColumn

		{

			DataPropertyName = "ContractStr",

			HeaderText = "Koniec kontraktu",

			Width = 115

		});

		this.gridPlayers.SelectionChanged += new System.EventHandler(this.gridPlayers_SelectionChanged);

		this.gridPlayers.CellDoubleClick += (object sender, System.Windows.Forms.DataGridViewCellEventArgs e) =>

		{

			if (e.RowIndex >= 0 && this.gridPlayers.Rows[e.RowIndex].DataBoundItem is FM08_Database_Editor.PlayerRecord)

			{

				this.ShowEditPlayerDialog((FM08_Database_Editor.PlayerRecord)this.gridPlayers.Rows[e.RowIndex].DataBoundItem);

			}

		};

		System.Windows.Forms.ContextMenuStrip gridCtx = new System.Windows.Forms.ContextMenuStrip();

		System.Windows.Forms.ToolStripMenuItem ctxItemEdit = new System.Windows.Forms.ToolStripMenuItem("Edytuj profil zawodnika...", null, (object s, System.EventArgs e) =>

		{

			if (this.gridPlayers.SelectedRows.Count > 0 && this.gridPlayers.SelectedRows[0].DataBoundItem is FM08_Database_Editor.PlayerRecord)

			{

				this.ShowEditPlayerDialog((FM08_Database_Editor.PlayerRecord)this.gridPlayers.SelectedRows[0].DataBoundItem);

			}

		});

		ctxItemEdit.Font = new System.Drawing.Font("Segoe UI", 9f, System.Drawing.FontStyle.Bold);

		gridCtx.Items.Add(ctxItemEdit);

		this.gridPlayers.ContextMenuStrip = gridCtx;

		this.gridPlayers.ColumnHeaderMouseClick += new System.Windows.Forms.DataGridViewCellMouseEventHandler(this.gridPlayers_ColumnHeaderMouseClick);

		mainSplit.Panel1.Controls.Add(this.gridPlayers);

		System.Windows.Forms.Panel panel5 = new System.Windows.Forms.Panel();

		panel5.Dock = System.Windows.Forms.DockStyle.Fill;

		panel5.BackColor = System.Drawing.Color.FromArgb(242, 245, 249);

		System.Windows.Forms.Panel panel6 = panel5;

		System.Windows.Forms.Panel panel7 = new System.Windows.Forms.Panel();

		panel7.Dock = System.Windows.Forms.DockStyle.Top;

		panel7.Height = 62;

		panel7.BackColor = System.Drawing.Color.FromArgb(24, 46, 73);

		panel7.Padding = new System.Windows.Forms.Padding(12, 4, 12, 4);

		System.Windows.Forms.Panel panel8 = panel7;

		System.Windows.Forms.Panel panel9 = new System.Windows.Forms.Panel();

		panel9.Dock = System.Windows.Forms.DockStyle.Right;

		panel9.Width = 460;

		panel9.BackColor = System.Drawing.Color.Transparent;

		System.Windows.Forms.Panel panel10 = panel9;

		this.lblDetailMetaInfo = new System.Windows.Forms.Label

		{

			Text = "",

			Dock = System.Windows.Forms.DockStyle.Top,

			Height = 26,

			TextAlign = System.Drawing.ContentAlignment.MiddleRight,

			Font = new System.Drawing.Font("Segoe UI", 9.5f, System.Drawing.FontStyle.Bold),

			ForeColor = System.Drawing.Color.FromArgb(255, 215, 0)

		};

		this.lblDetailRepInfo = new System.Windows.Forms.Label

		{

			Text = "",

			Dock = System.Windows.Forms.DockStyle.Top,

			Height = 22,

			TextAlign = System.Drawing.ContentAlignment.MiddleRight,

			Font = new System.Drawing.Font("Segoe UI", 8.5f, System.Drawing.FontStyle.Regular),

			ForeColor = System.Drawing.Color.FromArgb(200, 225, 255)

		};

		this.btnEditPlayer = new System.Windows.Forms.Button

		{

			Text = "Edytuj zawodnika...",

			Dock = System.Windows.Forms.DockStyle.Bottom,

			Height = 26,

			Font = new System.Drawing.Font("Segoe UI", 8.5f, System.Drawing.FontStyle.Bold),

			BackColor = System.Drawing.Color.FromArgb(240, 245, 255),

			FlatStyle = System.Windows.Forms.FlatStyle.System,

			Enabled = false

		};

		this.btnEditPlayer.Click += (object s, System.EventArgs e) =>

		{

			if (this.gridPlayers.SelectedRows.Count > 0)

			{

				this.ShowEditPlayerDialog((FM08_Database_Editor.PlayerRecord)this.gridPlayers.SelectedRows[0].DataBoundItem);

			}

		};

		panel10.Controls.Add(this.btnEditPlayer);

		panel10.Controls.Add(this.lblDetailRepInfo);

		panel10.Controls.Add(this.lblDetailMetaInfo);

		System.Windows.Forms.Panel panel11 = new System.Windows.Forms.Panel();

		panel11.Dock = System.Windows.Forms.DockStyle.Fill;

		panel11.BackColor = System.Drawing.Color.Transparent;

		System.Windows.Forms.Panel panel12 = panel11;

		this.lblDetailFullName = new System.Windows.Forms.Label

		{

			Text = "Wybierz zawodnika z listy powyżej...",

			Dock = System.Windows.Forms.DockStyle.Top,

			Height = 28,

			Font = new System.Drawing.Font("Segoe UI", 12f, System.Drawing.FontStyle.Bold),

			ForeColor = System.Drawing.Color.White

		};

		this.lblDetailSubInfo = new System.Windows.Forms.Label

		{

			Text = "Kliknij dowolny wiersz tabeli, aby wyświetlić pełne statystyki zawodnika.",

			Dock = System.Windows.Forms.DockStyle.Top,

			Height = 22,

			Font = new System.Drawing.Font("Segoe UI", 9f, System.Drawing.FontStyle.Regular),

			ForeColor = System.Drawing.Color.FromArgb(190, 215, 245)

		};

		panel12.Controls.Add(this.lblDetailSubInfo);

		panel12.Controls.Add(this.lblDetailFullName);

		panel8.Controls.Add(panel12);

		panel8.Controls.Add(panel10);

		System.Windows.Forms.TabControl tabControl = new System.Windows.Forms.TabControl();

		tabControl.Dock = System.Windows.Forms.DockStyle.Fill;

		tabControl.Font = new System.Drawing.Font("Segoe UI", 9f, System.Drawing.FontStyle.Regular);

		tabControl.Padding = new System.Drawing.Point(14, 6);

		System.Windows.Forms.TabControl tabControl2 = tabControl;

		System.Windows.Forms.TabPage tabPage = new System.Windows.Forms.TabPage("  Profil i Atrybuty (Styl FM)  ");

		tabPage.BackColor = System.Drawing.Color.FromArgb(242, 245, 249);

		tabPage.Padding = new System.Windows.Forms.Padding(8);

		System.Windows.Forms.TabPage tabPage2 = tabPage;

		System.Windows.Forms.TableLayoutPanel tableLayoutPanel = new System.Windows.Forms.TableLayoutPanel();

		tableLayoutPanel.Dock = System.Windows.Forms.DockStyle.Fill;

		tableLayoutPanel.ColumnCount = 3;

		tableLayoutPanel.RowCount = 1;

		tableLayoutPanel.BackColor = System.Drawing.Color.Transparent;

		System.Windows.Forms.TableLayoutPanel tableLayoutPanel2 = tableLayoutPanel;

		tableLayoutPanel2.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 34f));

		tableLayoutPanel2.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 33f));

		tableLayoutPanel2.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 33f));

		System.Windows.Forms.Panel body;

		System.Windows.Forms.Panel control = FM08_Database_Editor.CreateCardPanel("ATRYBUTY TECHNICZNE", out body);

		this.valCrossing = FM08_Database_Editor.AddCardRow(body, "Dośrodkowania", 0);

		this.valDribbling = FM08_Database_Editor.AddCardRow(body, "Drybling", 1);

		this.valFinishing = FM08_Database_Editor.AddCardRow(body, "Wykańczanie akcji", 2);

		this.valHeading = FM08_Database_Editor.AddCardRow(body, "Gra głową", 3);

		this.valLongShots = FM08_Database_Editor.AddCardRow(body, "Strzały z dystansu", 4);

		this.valMarking = FM08_Database_Editor.AddCardRow(body, "Krycie", 5);

		this.valMovement = FM08_Database_Editor.AddCardRow(body, "Gra bez piłki", 6);

		this.valPassing = FM08_Database_Editor.AddCardRow(body, "Podania", 7);

		this.valPenalties = FM08_Database_Editor.AddCardRow(body, "Rzuty karne", 8);

		this.valTackling = FM08_Database_Editor.AddCardRow(body, "Odbiory", 9);

		this.valCreativity = FM08_Database_Editor.AddCardRow(body, "Kreatywność", 10);

		this.valFirstTouch = FM08_Database_Editor.AddCardRow(body, "Pierwsze dotknięcie", 11);

		this.valTechnique = FM08_Database_Editor.AddCardRow(body, "Technika", 12);

		this.valCorners = FM08_Database_Editor.AddCardRow(body, "Rzuty rożne", 13);

		this.valFreeKicks = FM08_Database_Editor.AddCardRow(body, "Rzuty wolne", 14);

		this.valLongThrows = FM08_Database_Editor.AddCardRow(body, "Długie wyrzuty", 15);

		this.valVersatility = FM08_Database_Editor.AddCardRow(body, "Wszechstronność", 16);

		System.Windows.Forms.Panel body2;

		System.Windows.Forms.Panel control2 = FM08_Database_Editor.CreateCardPanel("ATRYBUTY PSYCHICZNE", out body2);

		this.valAggression = FM08_Database_Editor.AddCardRow(body2, "Agresja", 0);

		this.valAnticipation = FM08_Database_Editor.AddCardRow(body2, "Antycypacja", 1);

		this.valBravery = FM08_Database_Editor.AddCardRow(body2, "Odwaga", 2);

		this.valComposure = FM08_Database_Editor.AddCardRow(body2, "Opanowanie", 3);

		this.valConcentration = FM08_Database_Editor.AddCardRow(body2, "Koncentracja", 4);

		this.valConsistency = FM08_Database_Editor.AddCardRow(body2, "Konsekwencja", 5);

		this.valDecisions = FM08_Database_Editor.AddCardRow(body2, "Decyzje", 6);

		this.valDirtiness = FM08_Database_Editor.AddCardRow(body2, "Gra na faul", 7);

		this.valFlair = FM08_Database_Editor.AddCardRow(body2, "Błyskotliwość", 8);

		this.valImportantMatches = FM08_Database_Editor.AddCardRow(body2, "Ważne mecze", 9);

		this.valLeadership = FM08_Database_Editor.AddCardRow(body2, "Przywództwo", 10);

		this.valPositioning = FM08_Database_Editor.AddCardRow(body2, "Ustawianie się", 11);

		this.valTeamwork = FM08_Database_Editor.AddCardRow(body2, "Współpraca", 12);

		this.valWorkRate = FM08_Database_Editor.AddCardRow(body2, "Pracowitość", 13);

		System.Windows.Forms.Panel body3;

		System.Windows.Forms.Panel control3 = FM08_Database_Editor.CreateCardPanel("ATRYBUTY FIZYCZNE & NOGA", out body3);

		this.valAcceleration = FM08_Database_Editor.AddCardRow(body3, "Przyspieszenie", 0);

		this.valPace = FM08_Database_Editor.AddCardRow(body3, "Szybkość", 1);

		this.valAgility = FM08_Database_Editor.AddCardRow(body3, "Zwinność", 2);

		this.valJumping = FM08_Database_Editor.AddCardRow(body3, "Skoczność", 3);

		this.valBalance = FM08_Database_Editor.AddCardRow(body3, "Równowaga", 4);

		this.valStrength = FM08_Database_Editor.AddCardRow(body3, "Siła", 5);

		this.valStamina = FM08_Database_Editor.AddCardRow(body3, "Wytrzymałość", 6);

		this.valNaturalFitness = FM08_Database_Editor.AddCardRow(body3, "Sprawność ogólna", 7);

		this.valInjuryProneness = FM08_Database_Editor.AddCardRow(body3, "Podatność na kontuzje", 8);

		FM08_Database_Editor.AddCardSectionHeader(body3, "-- PREFEROWANA NOGA --", 9);

		this.valLeftFoot = FM08_Database_Editor.AddCardRow(body3, "Lewa noga", 10);

		this.valRightFoot = FM08_Database_Editor.AddCardRow(body3, "Prawa noga", 11);

		tableLayoutPanel2.Controls.Add(control, 0, 0);

		tableLayoutPanel2.Controls.Add(control2, 1, 0);

		tableLayoutPanel2.Controls.Add(control3, 2, 0);

		tabPage2.Controls.Add(tableLayoutPanel2);

		System.Windows.Forms.TabPage tabPage3 = new System.Windows.Forms.TabPage("  Atrybuty Bramkarskie  ");

		tabPage3.BackColor = System.Drawing.Color.FromArgb(242, 245, 249);

		tabPage3.Padding = new System.Windows.Forms.Padding(12);

		System.Windows.Forms.TabPage tabPage4 = tabPage3;

		System.Windows.Forms.TableLayoutPanel tableLayoutPanel3 = new System.Windows.Forms.TableLayoutPanel();

		tableLayoutPanel3.Dock = System.Windows.Forms.DockStyle.Fill;

		tableLayoutPanel3.ColumnCount = 2;

		tableLayoutPanel3.RowCount = 1;

		tableLayoutPanel3.BackColor = System.Drawing.Color.Transparent;

		System.Windows.Forms.TableLayoutPanel tableLayoutPanel4 = tableLayoutPanel3;

		tableLayoutPanel4.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 50f));

		tableLayoutPanel4.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 50f));

		System.Windows.Forms.Panel body4;

		System.Windows.Forms.Panel control4 = FM08_Database_Editor.CreateCardPanel("ATRYBUTY BRAMKARSKIE", out body4);

		this.valReflexes = FM08_Database_Editor.AddCardRow(body4, "Refleks", 0);

		this.valHandling = FM08_Database_Editor.AddCardRow(body4, "Chwytanie", 1);

		this.valOneOnOnes = FM08_Database_Editor.AddCardRow(body4, "Jeden na jednego", 2);

		this.valAerialAbility = FM08_Database_Editor.AddCardRow(body4, "Gra w powietrzu", 3);

		this.valCommandOfArea = FM08_Database_Editor.AddCardRow(body4, "Dowodzenie w polu", 4);

		this.valCommunication = FM08_Database_Editor.AddCardRow(body4, "Komunikacja", 5);

		this.valEccentricity = FM08_Database_Editor.AddCardRow(body4, "Ekscentryczność", 6);

		this.valKicking = FM08_Database_Editor.AddCardRow(body4, "Wykopy", 7);

		this.valRushingOut = FM08_Database_Editor.AddCardRow(body4, "Wyjścia z bramki", 8);

		this.valThrowing = FM08_Database_Editor.AddCardRow(body4, "Wyrzuty", 9);

		this.valTendencyToPunch = FM08_Database_Editor.AddCardRow(body4, "Piąstkowanie", 10);

		System.Windows.Forms.Panel body5;

		System.Windows.Forms.Panel control5 = FM08_Database_Editor.CreateCardPanel("CECHY UKRYTE", out body5);

		this.valHiddenConsistency = FM08_Database_Editor.AddCardRow(body5, "Konsekwencja", 0);

		this.valHiddenImpMatches = FM08_Database_Editor.AddCardRow(body5, "Ważne mecze", 1);

		this.valHiddenDirtiness = FM08_Database_Editor.AddCardRow(body5, "Gra na faul", 2);

		this.valHiddenVersatility = FM08_Database_Editor.AddCardRow(body5, "Wszechstronność", 3);

		this.valHiddenInjury = FM08_Database_Editor.AddCardRow(body5, "Podatność na kontuzje", 4);

		tableLayoutPanel4.Controls.Add(control4, 0, 0);

		tableLayoutPanel4.Controls.Add(control5, 1, 0);

		tabPage4.Controls.Add(tableLayoutPanel4);

		System.Windows.Forms.TabPage tabPage5 = new System.Windows.Forms.TabPage("  Pozycje na boisku  ");

		tabPage5.BackColor = System.Drawing.Color.FromArgb(242, 245, 249);

		tabPage5.Padding = new System.Windows.Forms.Padding(12);

		System.Windows.Forms.TabPage tabPage6 = tabPage5;

		System.Windows.Forms.TableLayoutPanel tableLayoutPanel5 = new System.Windows.Forms.TableLayoutPanel();

		tableLayoutPanel5.Dock = System.Windows.Forms.DockStyle.Fill;

		tableLayoutPanel5.ColumnCount = 2;

		tableLayoutPanel5.RowCount = 1;

		tableLayoutPanel5.BackColor = System.Drawing.Color.Transparent;

		System.Windows.Forms.TableLayoutPanel tableLayoutPanel6 = tableLayoutPanel5;

		tableLayoutPanel6.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 50f));

		tableLayoutPanel6.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 50f));

		System.Windows.Forms.Panel body6;

		System.Windows.Forms.Panel control6 = FM08_Database_Editor.CreateCardPanel("POZYCJE DEFENSYWNE I BRAMKARZ", out body6);

		this.valPosGK = FM08_Database_Editor.AddCardPositionRow(body6, "Bramkarz (GK)", 0);

		this.valPosSW = FM08_Database_Editor.AddCardPositionRow(body6, "Libero (SW)", 1);

		this.valPosDL = FM08_Database_Editor.AddCardPositionRow(body6, "Lewy obrońca (DL)", 2);

		this.valPosDC = FM08_Database_Editor.AddCardPositionRow(body6, "Środkowy obrońca (DC)", 3);

		this.valPosDR = FM08_Database_Editor.AddCardPositionRow(body6, "Prawy obrońca (DR)", 4);

		this.valPosDM = FM08_Database_Editor.AddCardPositionRow(body6, "Defensywny pomocnik (DM)", 5);

		this.valPosWBL = FM08_Database_Editor.AddCardPositionRow(body6, "Lewy wahadłowy (WBL)", 6);

		this.valPosWBR = FM08_Database_Editor.AddCardPositionRow(body6, "Prawy wahadłowy (WBR)", 7);

		System.Windows.Forms.Panel body7;

		System.Windows.Forms.Panel control7 = FM08_Database_Editor.CreateCardPanel("POZYCJE POMOCY I ATAKU", out body7);

		this.valPosML = FM08_Database_Editor.AddCardPositionRow(body7, "Lewy pomocnik (ML)", 0);

		this.valPosMC = FM08_Database_Editor.AddCardPositionRow(body7, "Środkowy pomocnik (MC)", 1);

		this.valPosMR = FM08_Database_Editor.AddCardPositionRow(body7, "Prawy pomocnik (MR)", 2);

		this.valPosAML = FM08_Database_Editor.AddCardPositionRow(body7, "Ofensywny pomocnik lewy / Skrzydłowy (AML)", 3);

		this.valPosAMC = FM08_Database_Editor.AddCardPositionRow(body7, "Ofensywny pomocnik środkowy (AMC)", 4);

		this.valPosAMR = FM08_Database_Editor.AddCardPositionRow(body7, "Ofensywny pomocnik prawy / Skrzydłowy (AMR)", 5);

		this.valPosST = FM08_Database_Editor.AddCardPositionRow(body7, "Napastnik (ST)", 6);

		this.valFreeRole = FM08_Database_Editor.AddCardPositionRow(body7, "Wolna rola (Free Role)", 7);

		tableLayoutPanel6.Controls.Add(control6, 0, 0);

		tableLayoutPanel6.Controls.Add(control7, 1, 0);

		tabPage6.Controls.Add(tableLayoutPanel6);

		tabControl2.TabPages.Add(tabPage2);

		tabControl2.TabPages.Add(tabPage4);

		tabControl2.TabPages.Add(tabPage6);

		panel6.Controls.Add(tabControl2);

		panel6.Controls.Add(panel8);

		panel8.SendToBack();

		mainSplit.Panel2.Controls.Add(panel6);

		System.Windows.Forms.Panel panel13 = new System.Windows.Forms.Panel();

		panel13.Dock = System.Windows.Forms.DockStyle.Fill;

		panel13.Padding = new System.Windows.Forms.Padding(15, 5, 15, 5);

		panel13.BackColor = System.Drawing.Color.FromArgb(245, 247, 250);

		System.Windows.Forms.Panel panel14 = panel13;

		panel14.Controls.Add(mainSplit);

		this.statusStrip = new System.Windows.Forms.StatusStrip();

		this.statusPlayerDetails = new System.Windows.Forms.ToolStripStatusLabel

		{

			Text = "Wybierz zawodnika, aby zobaczyć szczegóły.",

			Spring = true,

			TextAlign = System.Drawing.ContentAlignment.MiddleLeft

		};

		this.statusStrip.Items.Add(this.statusPlayerDetails);

		this.loaderWorker = new System.ComponentModel.BackgroundWorker

		{

			WorkerReportsProgress = true

		};

		this.loaderWorker.DoWork += new System.ComponentModel.DoWorkEventHandler(this.loaderWorker_DoWork);

		this.loaderWorker.ProgressChanged += new System.ComponentModel.ProgressChangedEventHandler(this.loaderWorker_ProgressChanged);

		this.loaderWorker.RunWorkerCompleted += new System.ComponentModel.RunWorkerCompletedEventHandler(this.loaderWorker_RunWorkerCompleted);

		this.mainMenu = this.CreateAppMenu();

		base.MainMenuStrip = this.mainMenu;

		base.Controls.Add(panel14);

		base.Controls.Add(panel4);

		base.Controls.Add(panel2);

		base.Controls.Add(this.mainMenu);

		base.Controls.Add(this.statusStrip);

	}



	private static Panel CreateCardPanel(string title, out Panel body)

	{

		Panel panel = new Panel();

		panel.Dock = DockStyle.Fill;

		panel.BackColor = Color.White;

		panel.Margin = new Padding(4);

		panel.BorderStyle = BorderStyle.FixedSingle;

		Panel panel2 = panel;

		Label label = new Label();

		label.Text = "  " + title;

		label.Dock = DockStyle.Top;

		label.Height = 26;

		label.BackColor = Color.FromArgb(24, 46, 73);

		label.ForeColor = Color.White;

		label.Font = new Font("Segoe UI", 9f, FontStyle.Bold);

		label.TextAlign = ContentAlignment.MiddleLeft;

		Label value = label;

		panel2.Controls.Add(value);

		body = new Panel

		{

			Dock = DockStyle.Fill,

			BackColor = Color.White,

			AutoScroll = true,

			Padding = new Padding(0)

		};

		panel2.Controls.Add(body);

		body.BringToFront();

		return panel2;

	}



	private static Label AddCardRow(Panel body, string name, int rowIndex)

	{

		Panel panel = new Panel();

		panel.Dock = DockStyle.Top;

		panel.Height = 21;

		panel.BackColor = ((rowIndex % 2 == 1) ? Color.FromArgb(248, 250, 253) : Color.White);

		Panel panel2 = panel;

		Label label = new Label();

		label.Text = "-";

		label.Dock = DockStyle.Right;

		label.Width = 46;

		label.TextAlign = ContentAlignment.MiddleRight;

		label.Font = fontBold;

		label.ForeColor = Color.FromArgb(120, 120, 120);

		label.Padding = new Padding(0, 0, 8, 0);

		Label label2 = label;

		Label label3 = new Label();

		label3.Text = name;

		label3.Dock = DockStyle.Fill;

		label3.TextAlign = ContentAlignment.MiddleLeft;

		label3.Font = fontRegular;

		label3.ForeColor = Color.FromArgb(35, 35, 35);

		label3.Padding = new Padding(8, 0, 0, 0);

		Label value = label3;

		panel2.Controls.Add(value);

		panel2.Controls.Add(label2);

		body.Controls.Add(panel2);

		panel2.BringToFront();

		return label2;

	}



	private static void AddCardSectionHeader(Panel body, string title, int rowIndex)

	{

		Panel panel = new Panel();

		panel.Dock = DockStyle.Top;

		panel.Height = 22;

		panel.BackColor = Color.FromArgb(232, 238, 245);

		Panel panel2 = panel;

		Label label = new Label();

		label.Text = title;

		label.Dock = DockStyle.Fill;

		label.TextAlign = ContentAlignment.MiddleCenter;

		label.Font = new Font("Segoe UI", 8f, FontStyle.Bold);

		label.ForeColor = Color.FromArgb(60, 75, 95);

		Label value = label;

		panel2.Controls.Add(value);

		body.Controls.Add(panel2);

		panel2.BringToFront();

	}



	private static Label AddCardPositionRow(Panel body, string name, int rowIndex)

	{

		Panel panel = new Panel();

		panel.Dock = DockStyle.Top;

		panel.Height = 25;

		panel.BackColor = ((rowIndex % 2 == 1) ? Color.FromArgb(248, 250, 253) : Color.White);

		Panel panel2 = panel;

		Label label = new Label();

		label.Text = "-";

		label.Dock = DockStyle.Right;

		label.Width = 145;

		label.TextAlign = ContentAlignment.MiddleRight;

		label.Font = fontBold;

		label.ForeColor = Color.FromArgb(120, 120, 120);

		label.Padding = new Padding(0, 0, 10, 0);

		Label label2 = label;

		Label label3 = new Label();

		label3.Text = name;

		label3.Dock = DockStyle.Fill;

		label3.TextAlign = ContentAlignment.MiddleLeft;

		label3.Font = fontRegular;

		label3.ForeColor = Color.FromArgb(35, 35, 35);

		label3.Padding = new Padding(10, 0, 0, 0);

		Label value = label3;

		panel2.Controls.Add(value);

		panel2.Controls.Add(label2);

		body.Controls.Add(panel2);

		panel2.BringToFront();

		return label2;

	}



	private static void SetAttrValue(Label lbl, byte val)

	{

		if (lbl == null)

		{

			return;

		}

		if (val == 0)

		{

			lbl.Text = "-";

			lbl.ForeColor = Color.FromArgb(170, 175, 180);

			lbl.Font = fontRegular;

			return;

		}

		lbl.Text = val.ToString();

		lbl.Font = fontBold;

		if (val >= 16)

		{

			lbl.ForeColor = Color.FromArgb(0, 135, 30);

		}

		else if (val >= 11)

		{

			lbl.ForeColor = Color.FromArgb(0, 80, 195);

		}

		else

		{

			lbl.ForeColor = Color.FromArgb(50, 50, 50);

		}

	}



	private static void SetPosValue(Label lbl, byte val)

	{

		if (lbl == null)

		{

			return;

		}

		if (val == 0)

		{

			lbl.Text = "- (0)";

			lbl.ForeColor = Color.FromArgb(160, 160, 160);

			lbl.Font = fontRegular;

			return;

		}

		string text = "Nieprzeszkolony";

		if (val == 20)

		{

			text = "Naturalna";

		}

		else if (val >= 15)

		{

			text = "Zdolny";

		}

		else

		{

			text = ((val < 10) ? "Słaba" : "Przeszkolony");

		}

		lbl.Text = string.Format("{0} ({1})", text, val);

		if (val == 20)

		{

			lbl.ForeColor = Color.FromArgb(0, 130, 0);

			lbl.Font = fontBold;

		}

		else if (val >= 15)

		{

			lbl.ForeColor = Color.FromArgb(34, 139, 34);

			lbl.Font = fontBold;

		}

		else if (val >= 10)

		{

			lbl.ForeColor = Color.FromArgb(0, 75, 190);

			lbl.Font = fontBold;

		}

		else

		{

			lbl.ForeColor = Color.FromArgb(90, 90, 90);

			lbl.Font = fontRegular;

		}

	}



	private void DisplayPlayerDetails(PlayerRecord p)

	{

		if (p != null)

		{

			lblDetailFullName.Text = string.Format("{0} (ID: {1})", p.FullName, p.Id);

			lblDetailSubInfo.Text = string.Format("Klub: {0} | Pozycja: {1} | Wiek: {2} ({3}) | Narodowość: {4}", string.IsNullOrEmpty(p.Club) ? "Brak (wolny agent)" : p.Club, string.IsNullOrEmpty(p.Position) ? "-" : p.Position, (p.Age > 0) ? p.Age.ToString() : "-", p.BirthDateStr, string.IsNullOrEmpty(p.Nationality) ? "-" : p.Nationality);

			lblDetailMetaInfo.Text = string.Format("CA: {0} | PA: {1} | Wzrost: {2} | Waga: {3}", p.CA, p.PA, p.HeightStr, p.WeightStr);

			lblDetailRepInfo.Text = string.Format("Rep (B/K/Ś): {0} | Noga: {1} | Kontrakt: {2}", p.ReputationStr, p.PreferredFootStr, p.ContractStr);

			SetAttrValue(valCrossing, p.Crossing);

			SetAttrValue(valDribbling, p.Dribbling);

			SetAttrValue(valFinishing, p.Finishing);

			SetAttrValue(valHeading, p.Heading);

			SetAttrValue(valLongShots, p.LongShots);

			SetAttrValue(valMarking, p.Marking);

			SetAttrValue(valMovement, p.Movement);

			SetAttrValue(valPassing, p.Passing);

			SetAttrValue(valPenalties, p.Penalties);

			SetAttrValue(valTackling, p.Tackling);

			SetAttrValue(valCreativity, p.Creativity);

			SetAttrValue(valFirstTouch, p.FirstTouch);

			SetAttrValue(valTechnique, p.Technique);

			SetAttrValue(valCorners, p.Corners);

			SetAttrValue(valLongThrows, p.LongThrows);

			SetAttrValue(valFreeKicks, p.FreeKicks);

			SetAttrValue(valVersatility, p.Versatility);

			SetAttrValue(valAggression, p.Aggression);

			SetAttrValue(valAnticipation, p.Anticipation);

			SetAttrValue(valBravery, p.Bravery);

			SetAttrValue(valComposure, p.Composure);

			SetAttrValue(valConcentration, p.Concentration);

			SetAttrValue(valConsistency, p.Consistency);

			SetAttrValue(valDecisions, p.Decisions);

			SetAttrValue(valDirtiness, p.Dirtiness);

			SetAttrValue(valFlair, p.Flair);

			SetAttrValue(valImportantMatches, p.ImportantMatches);

			SetAttrValue(valLeadership, p.Leadership);

			SetAttrValue(valPositioning, p.Positioning);

			SetAttrValue(valTeamwork, p.Teamwork);

			SetAttrValue(valWorkRate, p.WorkRate);

			SetAttrValue(valAcceleration, p.Acceleration);

			SetAttrValue(valAgility, p.Agility);

			SetAttrValue(valBalance, p.Balance);

			SetAttrValue(valInjuryProneness, p.InjuryProneness);

			SetAttrValue(valJumping, p.Jumping);

			SetAttrValue(valNaturalFitness, p.NaturalFitness);

			SetAttrValue(valPace, p.Pace);

			SetAttrValue(valStamina, p.Stamina);

			SetAttrValue(valStrength, p.Strength);

			SetAttrValue(valLeftFoot, p.LeftFoot);

			SetAttrValue(valRightFoot, p.RightFoot);

			SetAttrValue(valAerialAbility, p.AerialAbility);

			SetAttrValue(valCommandOfArea, p.CommandOfArea);

			SetAttrValue(valCommunication, p.Communication);

			SetAttrValue(valEccentricity, p.Eccentricity);

			SetAttrValue(valHandling, p.Handling);

			SetAttrValue(valKicking, p.Kicking);

			SetAttrValue(valOneOnOnes, p.OneOnOnes);

			SetAttrValue(valReflexes, p.Reflexes);

			SetAttrValue(valRushingOut, p.RushingOut);

			SetAttrValue(valThrowing, p.Throwing);

			SetAttrValue(valTendencyToPunch, p.TendencyToPunch);

			SetAttrValue(valHiddenConsistency, p.Consistency);

			SetAttrValue(valHiddenImpMatches, p.ImportantMatches);

			SetAttrValue(valHiddenDirtiness, p.Dirtiness);

			SetAttrValue(valHiddenVersatility, p.Versatility);

			SetAttrValue(valHiddenInjury, p.InjuryProneness);

			SetPosValue(valPosGK, p.PosGK);

			SetPosValue(valPosSW, p.PosSW);

			SetPosValue(valPosDL, p.PosDL);

			SetPosValue(valPosDC, p.PosDC);

			SetPosValue(valPosDR, p.PosDR);

			SetPosValue(valPosDM, p.PosDM);

			SetPosValue(valPosWBL, p.PosWBL);

			SetPosValue(valPosWBR, p.PosWBR);

			SetPosValue(valPosML, p.PosML);

			SetPosValue(valPosMC, p.PosMC);

			SetPosValue(valPosMR, p.PosMR);

			SetPosValue(valPosAML, p.PosAML);

			SetPosValue(valPosAMC, p.PosAMC);

			SetPosValue(valPosAMR, p.PosAMR);

			SetPosValue(valPosST, p.PosST);

			SetPosValue(valFreeRole, p.FreeRole);

		}

	}



	private void DetectDatabases()

	{

		cbDatabases.Items.Clear();

		string text = "D:\\Gry\\FM08\\Dane\\db";

		if (Directory.Exists(text))

		{

			string[] directories = Directory.GetDirectories(text);

			string[] array = directories;

			foreach (string path in array)

			{

				string fileName = Path.GetFileName(path);

				cbDatabases.Items.Add(fileName);

				if (fileName.Equals("8.0.2 Extended 0.7", StringComparison.OrdinalIgnoreCase))

				{

					cbDatabases.SelectedItem = fileName;

				}

			}

		}

		if (cbDatabases.SelectedIndex == -1 && cbDatabases.Items.Count > 0)

		{

			cbDatabases.SelectedIndex = 0;

		}

		if (cbDatabases.SelectedItem != null)

		{

			txtCustomPath.Text = Path.Combine(text, cbDatabases.SelectedItem.ToString());

		}

	}



	private void cbDatabases_SelectedIndexChanged(object sender, EventArgs e)

	{

		if (cbDatabases.SelectedItem != null)

		{

			txtCustomPath.Text = Path.Combine("D:\\Gry\\FM08\\Dane\\db", cbDatabases.SelectedItem.ToString());

		}

	}



	private void btnBrowse_Click(object sender, EventArgs e)

	{

		using (FolderBrowserDialog folderBrowserDialog = new FolderBrowserDialog())

		{

			folderBrowserDialog.SelectedPath = txtCustomPath.Text;

			if (folderBrowserDialog.ShowDialog() == DialogResult.OK)

			{

				txtCustomPath.Text = folderBrowserDialog.SelectedPath;

			}

		}

	}



	private void btnLoad_Click(object sender, EventArgs e)

	{

		string text = txtCustomPath.Text.Trim();

		if (!Directory.Exists(text))

		{

			MessageBox.Show("Wybrany folder bazy danych nie istnieje:\n" + text, "Błąd", MessageBoxButtons.OK, MessageBoxIcon.Exclamation);

			return;

		}

		btnLoad.Enabled = false;

		btnBrowse.Enabled = false;

		cbDatabases.Enabled = false;

		if (cbClubFilter != null)

		{

			cbClubFilter.Enabled = false;

			cbClubFilter.Items.Clear();

			cbClubFilter.Items.Add("-- Wczytywanie bazy... --");

			cbClubFilter.SelectedIndex = 0;

		}

		if (btnResetClub != null)

		{

			btnResetClub.Enabled = false;

		}

		progressBar.Value = 0;

		progressBar.Visible = true;

		lblStatus.Text = "Rozpoczynanie wczytywania bazy danych...";

		loaderWorker.RunWorkerAsync(text);

	}



	private void loaderWorker_DoWork(object sender, DoWorkEventArgs e)

	{

		string text = (string)e.Argument;

		loaderWorker.ReportProgress(10, "Dekompresja bazy server_db.dat...");

		string path = Path.Combine(text, "server_db.dat");

		byte[] serverDbHeader = (File.Exists(path) ? GetFileHeader(path) : null);

		byte[] array = (File.Exists(path) ? DecompressFile(path) : new byte[0]);

		loaderWorker.ReportProgress(30, "Dekompresja bazy people_db.dat...");

		string path2 = Path.Combine(text, "people_db.dat");

		byte[] peopleDbHeader = (File.Exists(path2) ? GetFileHeader(path2) : null);

		byte[] array2 = (File.Exists(path2) ? DecompressFile(path2) : new byte[0]);

		loaderWorker.ReportProgress(40, "Parsowanie nazw klubów...");

		Dictionary<int, string> clubs = ParseClubs(array);
		if (array2.Length >= 4) ResolveNativeU23ClubNames(array, BitConverter.ToInt32(array2, 0), clubs);

		loaderWorker.ReportProgress(48, "Parsowanie bazy narodowości...");

		Dictionary<int, string> nations = ParseNations(array);

		loaderWorker.ReportProgress(55, "Parsowanie słowników imion i nazwisk...");

		int fnStart;

		int snStart;

		Dictionary<int, string> firstNames = ParseFirstNames(array, out fnStart, out snStart);

		Dictionary<int, string> surnamesByPid;

		int cnStart;

		Dictionary<int, string> surnames = ParseSurnames(array, snStart, out surnamesByPid, out cnStart);

		Dictionary<int, string> commonNames = ParseCommonNames(array, cnStart);

		loaderWorker.ReportProgress(68, "Parsowanie drzewa encji i tagów...");

		Dictionary<int, string[]> namesByPid = ParseEntityTreeAndTags(array);

		loaderWorker.ReportProgress(80, "Parsowanie rekordów personalnych, dat urodzenia i kontraktów...");

		Dictionary<int, PersonDetails> personData = ParsePersonData(array2, firstNames, surnames, commonNames, clubs);

		loaderWorker.ReportProgress(92, "Budowanie bazy zawodników i obliczanie pozycji...");

		List<PlayerRecord> players = BuildPlayerList(array2, personData, namesByPid, surnamesByPid, clubs, nations);

		loaderWorker.ReportProgress(96, "Parsowanie oficjalnej bazy emerytur...");

		Dictionary<int, DateTime> retirements = ParseRetirements(array);

		foreach (var p in players)

		{

			DateTime rDate;

			if (retirements.TryGetValue(p.Id, out rDate))

			{

				p.RetirementDate = rDate;

			}

		}

		loaderWorker.ReportProgress(100, "Gotowe!");

		e.Result = new LoadDbResult

		{

			Players = players,

			PeopleDb = array2,

			PeopleDbHeader = peopleDbHeader,

			ServerDb = array,

			ServerDbHeader = serverDbHeader,

			DbDir = text,

			Clubs = clubs,

			Nations = nations

		};

	}



	private void loaderWorker_ProgressChanged(object sender, ProgressChangedEventArgs e)

	{

		progressBar.Value = Math.Min(100, Math.Max(0, e.ProgressPercentage));

		if (e.UserState != null)

		{

			lblStatus.Text = e.UserState.ToString();

		}

	}



	private void loaderWorker_RunWorkerCompleted(object sender, RunWorkerCompletedEventArgs e)

	{

		btnLoad.Enabled = true;

		btnBrowse.Enabled = true;

		cbDatabases.Enabled = true;

		progressBar.Visible = false;

		if (e.Error != null)

		{

			MessageBox.Show("Błąd podczas wczytywania bazy:\n" + e.Error.Message, "Błąd", MessageBoxButtons.OK, MessageBoxIcon.Hand);

			lblStatus.Text = "Błąd wczytywania bazy.";

			return;

		}

		LoadDbResult loadDbResult = (LoadDbResult)e.Result;

		allPlayers = loadDbResult.Players;

		loadedPeopleDbRaw = loadDbResult.PeopleDb;
		loadedClientDbRaw = null;
		loadedClientDbOrigHeader = null;

		LoadedClubs = loadDbResult.Clubs ?? new Dictionary<int, string>();

		LoadedNations = loadDbResult.Nations ?? new Dictionary<int, string>();

		ClubsRev.Clear();

		foreach (KeyValuePair<int, string> kvp in LoadedClubs)

		{

			if (!ClubsRev.ContainsKey(kvp.Value))

			{

				ClubsRev[kvp.Value] = kvp.Key;

			}

		}

		NationsRev.Clear();

		foreach (KeyValuePair<int, string> kvp in LoadedNations)

		{

			if (!NationsRev.ContainsKey(kvp.Value))

			{

				NationsRev[kvp.Value] = kvp.Key;

			}

		}

		LoadedAllPlayers = allPlayers ?? new List<PlayerRecord>();

		loadedPeopleDbOrigHeader = loadDbResult.PeopleDbHeader;

		loadedServerDbRaw = loadDbResult.ServerDb;

		loadedServerDbOrigHeader = loadDbResult.ServerDbHeader;

		loadedDbPath = loadDbResult.DbDir;

		hasUnsavedChanges = false;

		if (btnExportCsv != null)

		{

			btnExportCsv.Enabled = true;

		}

		if (btnImportCsv != null)

		{

			btnImportCsv.Enabled = true;

		}

		if (btnSaveDb != null)

		{

			btnSaveDb.Enabled = true;

		}

		if (btnEditPlayer != null)

		{

			btnEditPlayer.Enabled = true;

		}

		if (btnAddPlayer != null)

		{

			btnAddPlayer.Enabled = true;

		}

		lblStatus.Text = string.Format("Wczytano pomyślnie {0:N0} zawodników z bazy!", allPlayers.Count);

		HashSet<string> hashSet = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

		foreach (PlayerRecord allPlayer in allPlayers)

		{

			if (!string.IsNullOrEmpty(allPlayer.Club))

			{

				hashSet.Add(allPlayer.Club);

			}

		}

		List<string> list = new List<string>(hashSet);

		list.Sort(StringComparer.CurrentCultureIgnoreCase);

		cbClubFilter.BeginUpdate();

		cbClubFilter.Items.Clear();

		cbClubFilter.Items.Add("-- Wszystkie kluby --");

		cbClubFilter.Items.Add("[Bez klubu / Wolni agenci]");

		foreach (string item in list)

		{

			cbClubFilter.Items.Add(item);

		}

		cbClubFilter.SelectedIndex = 0;

		cbClubFilter.EndUpdate();

		cbClubFilter.Enabled = true;

		btnResetClub.Enabled = true;

		ApplyFilter();

	}



	private void cbClubFilter_SelectedIndexChanged(object sender, EventArgs e)

	{

		ApplyFilter();

	}



	private void cbClubFilter_KeyDown(object sender, KeyEventArgs e)

	{

		if (e.KeyCode == Keys.Return)

		{

			ApplyFilter();

			e.Handled = true;

			e.SuppressKeyPress = true;

		}

	}



	private void btnResetClub_Click(object sender, EventArgs e)

	{

		if (cbClubFilter.Items.Count > 0)

		{

			cbClubFilter.SelectedIndex = 0;

		}

		ApplyFilter();

	}



	private void txtSearch_TextChanged(object sender, EventArgs e)

	{

		ApplyFilter();

	}



	private void gridPlayers_ColumnHeaderMouseClick(object sender, DataGridViewCellMouseEventArgs e)

	{

		if (filteredPlayers == null || filteredPlayers.Count == 0 || e.ColumnIndex < 0)

		{

			return;

		}

		string dataPropertyName = gridPlayers.Columns[e.ColumnIndex].DataPropertyName;

		if (dataPropertyName == lastSortColumn)

		{

			sortAscending = !sortAscending;

		}

		else

		{

			lastSortColumn = dataPropertyName;

			sortAscending = true;

		}

		switch (dataPropertyName)

		{

		case "Id":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) => sortAscending ? a.Id.CompareTo(b.Id) : b.Id.CompareTo(a.Id));

			break;

		case "FirstName":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) => sortAscending ? string.Compare(a.FirstName, b.FirstName) : string.Compare(b.FirstName, a.FirstName));

			break;

		case "LastName":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) => sortAscending ? string.Compare(a.LastName, b.LastName) : string.Compare(b.LastName, a.LastName));

			break;

		case "Position":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) => sortAscending ? string.Compare(a.Position, b.Position) : string.Compare(b.Position, a.Position));

			break;

		case "Age":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) => sortAscending ? a.Age.CompareTo(b.Age) : b.Age.CompareTo(a.Age));

			break;

		case "BirthDateStr":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) =>

			{

				DateTime value = a.BirthDate ?? DateTime.MinValue;

				DateTime value2 = b.BirthDate ?? DateTime.MinValue;

				return sortAscending ? value.CompareTo(value2) : value2.CompareTo(value);

			});

			break;

		case "Nationality":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) => sortAscending ? string.Compare(a.Nationality, b.Nationality) : string.Compare(b.Nationality, a.Nationality));

			break;

		case "Club":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) => sortAscending ? string.Compare(a.Club, b.Club) : string.Compare(b.Club, a.Club));

			break;

		case "CA":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) => sortAscending ? a.CA.CompareTo(b.CA) : b.CA.CompareTo(a.CA));

			break;

		case "PA":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) => sortAscending ? a.PA.CompareTo(b.PA) : b.PA.CompareTo(a.PA));

			break;

		case "ContractStr":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) =>

			{

				DateTime value = a.ContractExpires ?? DateTime.MaxValue;

				DateTime value2 = b.ContractExpires ?? DateTime.MaxValue;

				return sortAscending ? value.CompareTo(value2) : value2.CompareTo(value);

			});

			break;

		case "HeightStr":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) => sortAscending ? a.Height.CompareTo(b.Height) : b.Height.CompareTo(a.Height));

			break;

		case "WeightStr":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) => sortAscending ? a.Weight.CompareTo(b.Weight) : b.Weight.CompareTo(a.Weight));

			break;

		case "ReputationStr":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) => sortAscending ? a.CurrentReputation.CompareTo(b.CurrentReputation) : b.CurrentReputation.CompareTo(a.CurrentReputation));

			break;

		case "PreferredFootStr":

			filteredPlayers.Sort((PlayerRecord a, PlayerRecord b) => sortAscending ? string.Compare(a.PreferredFootStr, b.PreferredFootStr) : string.Compare(b.PreferredFootStr, a.PreferredFootStr));

			break;

		}

		gridPlayers.DataSource = null;

		gridPlayers.DataSource = filteredPlayers;

	}



	private static string NormalizeText(string s)

	{

		if (string.IsNullOrEmpty(s))

		{

			return "";

		}

		string text;

		try

		{

			text = s.Normalize(NormalizationForm.FormD);

		}

		catch

		{

			text = s;

		}

		StringBuilder stringBuilder = new StringBuilder(text.Length);

		string text2 = text;

		foreach (char c in text2)

		{

			try

			{

				UnicodeCategory unicodeCategory = CharUnicodeInfo.GetUnicodeCategory(c);

				if (unicodeCategory != UnicodeCategory.NonSpacingMark)

				{

					if (c == 'ł' || c == 'Ř')

					{

						stringBuilder.Append('l');

					}

					else if (c == 'ø' || c == 'Ø')

					{

						stringBuilder.Append('o');

					}

					else if (c == 'æ' || c == 'Æ')

					{

						stringBuilder.Append('a');

						stringBuilder.Append('e');

					}

					else if (c == 'ß')

					{

						stringBuilder.Append('s');

						stringBuilder.Append('s');

					}

					else

					{

						stringBuilder.Append(char.ToLowerInvariant(c));

					}

				}

			}

			catch

			{

				stringBuilder.Append(char.ToLowerInvariant(c));

			}

		}

		return stringBuilder.ToString();

	}



	private void ApplyFilter()

	{

		if (allPlayers == null || allPlayers.Count == 0)

		{

			return;

		}

		string text = txtSearch.Text.Trim();

		bool flag = !string.IsNullOrEmpty(text);

		string value = NormalizeText(text);

		string text2 = "";

		bool flag2 = false;

		bool flag3 = false;

		if (cbClubFilter != null && cbClubFilter.SelectedItem != null)

		{

			string text3 = cbClubFilter.SelectedItem.ToString();

			if (text3.Equals("[Bez klubu / Wolni agenci]", StringComparison.OrdinalIgnoreCase))

			{

				flag2 = true;

			}

			else if (!text3.StartsWith("--"))

			{

				text2 = text3;

				flag3 = true;

			}

		}

		else if (cbClubFilter != null && !string.IsNullOrEmpty(cbClubFilter.Text))

		{

			string text4 = cbClubFilter.Text.Trim();

			if (!text4.StartsWith("--"))

			{

				text2 = text4;

				foreach (object item in cbClubFilter.Items)

				{

					if (item.ToString().Equals(text4, StringComparison.OrdinalIgnoreCase))

					{

						text2 = item.ToString();

						flag3 = true;

						break;

					}

				}

			}

		}

		bool flag4 = flag2 || !string.IsNullOrEmpty(text2);

		string value2 = NormalizeText(text2);

		if (!flag && !flag4)

		{

			int num = Math.Min(500, allPlayers.Count);

			filteredPlayers = allPlayers.GetRange(0, num);

			gridPlayers.DataSource = filteredPlayers;

			lblFoundCount.Text = string.Format("Wyświetlono pierwszych {0} z {1:N0} zawodników (wpisz frazę lub wybierz klub).", num, allPlayers.Count);

			return;

		}

		List<PlayerRecord> list = new List<PlayerRecord>();

		int num2 = 5000;

		foreach (PlayerRecord allPlayer in allPlayers)

		{

			if (flag4)

			{

				if (flag2)

				{

					if (!string.IsNullOrEmpty(allPlayer.Club))

					{

						continue;

					}

				}

				else

				{

					if (string.IsNullOrEmpty(allPlayer.Club))

					{

						continue;

					}

					if (flag3)

					{

						if (!allPlayer.Club.Equals(text2, StringComparison.OrdinalIgnoreCase))

						{

							continue;

						}

					}

					else if (!allPlayer.Club.Equals(text2, StringComparison.OrdinalIgnoreCase) && NormalizeText(allPlayer.Club).IndexOf(value2, StringComparison.Ordinal) < 0)

					{

						continue;

					}

				}

			}

			if (!flag || !(allPlayer.Id.ToString() != text) || NormalizeText(allPlayer.FullName).IndexOf(value, StringComparison.Ordinal) >= 0 || NormalizeText(allPlayer.Club).IndexOf(value, StringComparison.Ordinal) >= 0 || NormalizeText(allPlayer.Nationality).IndexOf(value, StringComparison.Ordinal) >= 0 || NormalizeText(allPlayer.Position).IndexOf(value, StringComparison.Ordinal) >= 0)

			{

				list.Add(allPlayer);

				if (list.Count >= num2)

				{

					break;

				}

			}

		}

		filteredPlayers = list;

		gridPlayers.DataSource = filteredPlayers;

		if (filteredPlayers.Count > 0)

		{

			DisplayPlayerDetails(filteredPlayers[0]);

		}

		if (flag4 && !flag)

		{

			string arg = (flag2 ? "Wolni agenci" : text2);

			lblFoundCount.Text = string.Format("Znaleziono: {0} zawodników w klubie: {1}.", filteredPlayers.Count, arg);

		}

		else if (flag4 && flag)

		{

			string arg = (flag2 ? "Wolni agenci" : text2);

			lblFoundCount.Text = string.Format("Znaleziono: {0} zawodników w klubie: {1} (szukaj: '{2}').", filteredPlayers.Count, arg, text);

		}

		else

		{

			lblFoundCount.Text = string.Format("Znaleziono: {0} pasujących zawodników (maks. {1}).", filteredPlayers.Count, num2);

		}

	}



	private void gridPlayers_SelectionChanged(object sender, EventArgs e)

	{

		if (gridPlayers.SelectedRows.Count > 0)

		{

			DataGridViewRow dataGridViewRow = gridPlayers.SelectedRows[0];

			PlayerRecord playerRecord = dataGridViewRow.DataBoundItem as PlayerRecord;

			if (playerRecord != null)

			{

				DisplayPlayerDetails(playerRecord);

				statusPlayerDetails.Text = string.Format("Zawodnik: {0} | Pozycja: {1} | Wiek: {2} ({3}) | Narodowość: {4} | Klub: {5} | Kontrakt: {6} | CA: {7} | PA: {8} | ID: {9}", playerRecord.FullName, string.IsNullOrEmpty(playerRecord.Position) ? "-" : playerRecord.Position, (playerRecord.Age > 0) ? playerRecord.Age.ToString() : "-", playerRecord.BirthDateStr, string.IsNullOrEmpty(playerRecord.Nationality) ? "-" : playerRecord.Nationality, string.IsNullOrEmpty(playerRecord.Club) ? "Brak (wolny agent)" : playerRecord.Club, playerRecord.ContractStr, playerRecord.CA, playerRecord.PA, playerRecord.Id);

			}

		}

	}



	private static byte[] DecompressFile(string path)

	{

		byte[] array = File.ReadAllBytes(path);

		if (array.Length < 16)

		{

			return array;

		}

		using (MemoryStream stream = new MemoryStream(array, 11, array.Length - 15))

		{

			using (DeflateStream deflateStream = new DeflateStream(stream, CompressionMode.Decompress))

			{

				using (MemoryStream memoryStream = new MemoryStream())

				{

					byte[] array2 = new byte[65536];

					int count;

					while ((count = deflateStream.Read(array2, 0, array2.Length)) > 0)

					{

						memoryStream.Write(array2, 0, count);

					}

					return memoryStream.ToArray();

				}

			}

		}

	}



	private static Dictionary<int, string> ParseClubs(byte[] srv)

	{

		Dictionary<int, string> dictionary = new Dictionary<int, string>();

		byte[] array = new byte[7] { 255, 0, 0, 108, 7, 0, 0 };

		for (int i = 0; i < srv.Length - 200; i++)

		{

			bool flag = true;

			for (int j = 0; j < array.Length; j++)

			{

				if (srv[i + j] != array[j])

				{

					flag = false;

					break;

				}

			}

			if (!flag)

			{

				continue;

			}

			int num = BitConverter.ToInt32(srv, i + 9);

			if (num < 2 || num > 50 || i + 13 + num * 2 + 2 > srv.Length)

			{

				continue;

			}

			string text = Encoding.Unicode.GetString(srv, i + 13, num * 2);

			bool flag2 = true;

			string text2 = text;

			foreach (char c in text2)

			{

				if (c < ' ' || c > '─')

				{

					flag2 = false;

					break;

				}

			}

			if (!flag2)

			{

				continue;

			}

			int num2 = i + 13 + num * 2 + 2;

			int num3 = BitConverter.ToInt32(srv, num2);

			int num4 = num2;

			string text3 = "";

			if (num3 >= 1 && num3 <= 35 && num2 + 4 + num3 * 2 + 2 <= srv.Length)

			{

				text3 = Encoding.Unicode.GetString(srv, num2 + 4, num3 * 2);

				num4 = num2 + 4 + num3 * 2 + 2;

			}

			int num5 = -1;

			if (num4 + 6 <= srv.Length && srv[num4] == 0 && (srv[num4 + 1] == 1 || srv[num4 + 1] == 2))

			{

				int num6 = BitConverter.ToInt32(srv, num4 + 2);

				if (num6 > 0 && num6 <= 25000 && num6 != 32767 && srv[num4 + 2] != 0 && srv[num4 + 4] == 0 && srv[num4 + 5] == 0)

				{

					num5 = num6;

				}

			}

			if (num5 <= 0)

			{

				for (int l = num4 + 2; l <= num4 + 50 && l + 4 <= srv.Length; l++)

				{

					byte b = srv[l - 1];

					byte b2 = (byte)((l >= num4 + 2) ? srv[l - 2] : 0);

					if ((b == 1 || b == 2 || b == 3) && b2 <= 32 && srv[l] != 0 && srv[l + 2] == 0 && srv[l + 3] == 0)

					{

						int num7 = BitConverter.ToInt32(srv, l);

						if (num7 > 0 && num7 <= 25000 && num7 != 32767)

						{

							num5 = num7;

						}

					}

				}

			}

			if (num5 > 0 && !dictionary.ContainsKey(num5))

			{

				dictionary[num5] = text;

			}

		}

		Dictionary<int, string> dictionary2 = new Dictionary<int, string>();

		dictionary2.Add(995, "Juventus");

		dictionary2.Add(1278, "Legia Warszawa");

		dictionary2.Add(1178, "Legia Warszawa");

		dictionary2.Add(993, "Inter");

		dictionary2.Add(994, "AC Milan");

		dictionary2.Add(997, "Roma");

		dictionary2.Add(996, "Napoli");

		dictionary2.Add(998, "Lazio");

		dictionary2.Add(992, "Fiorentina");

		dictionary2.Add(987, "Atalanta");

		dictionary2.Add(999, "Sampdoria");

		dictionary2.Add(1000, "Torino");

		dictionary2.Add(1491, "F.C. Barcelona");

		dictionary2.Add(1466, "F.C. Barcelona B");

		dictionary2.Add(212, "F.C. Barcelona C");

		dictionary2.Add(1734, "F.C. Barcelona");

		dictionary2.Add(1506, "Real Madrid");

		dictionary2.Add(1508, "Real Madrid Castilla");

		dictionary2.Add(1736, "Real Madrid");

		dictionary2.Add(1738, "Valencia");

		dictionary2.Add(1737, "Sevilla");

		dictionary2.Add(1735, "Atletico Madrid");

		dictionary2.Add(602, "Arsenal");

		dictionary2.Add(630, "Chelsea");

		dictionary2.Add(676, "Liverpool");

		dictionary2.Add(680, "Manchester United");

		dictionary2.Add(679, "Manchester City");

		dictionary2.Add(915, "Bayern Munich");

		dictionary2.Add(802, "FC Bayern München");

		dictionary2.Add(869, "Paris Saint-Germain");

		dictionary2.Add(1173, "Benfica");

		dictionary2.Add(1174, "Porto");

		dictionary2.Add(1175, "Sporting CP");

		dictionary2.Add(1109, "Ajax");

		dictionary2.Add(1110, "PSV");

		dictionary2.Add(1111, "Feyenoord");

		dictionary2.Add(1184, "Wisła Kraków");

		dictionary2.Add(1179, "Lech Poznań");

		dictionary2.Add(10726, "Málaga B");

		Dictionary<int, string> dictionary3 = dictionary2;

		foreach (KeyValuePair<int, string> item in dictionary3)

		{

			if (!dictionary.ContainsKey(item.Key))

			{

				dictionary[item.Key] = item.Value;

			}

		}

		return dictionary;

	}



	private static Dictionary<int, string> ParseNations(byte[] srv)

	{

		Dictionary<int, string> dictionary = new Dictionary<int, string>();

		if (srv.Length < 1000)

		{

			return dictionary;

		}

		byte[] array = new byte[14]

		{

			255, 255, 255, 255, 255, 255, 255, 255, 0, 0,

			0, 0, 0, 1

		};

		int i = 9000000;

		int num = 0;

		for (; i < 9600000 && i < srv.Length - 50; i++)

		{

			bool flag = true;

			for (int j = 0; j < array.Length; j++)

			{

				if (srv[i + j] != array[j])

				{

					flag = false;

					break;

				}

			}

			if (!flag)

			{

				continue;

			}

			for (int k = 14; k <= 16; k += 2)

			{

				int num2 = BitConverter.ToInt32(srv, i + k);

				if (num2 >= 3 && num2 <= 40 && i + k + 4 + num2 * 2 <= srv.Length)

				{

					try

					{

						string value = Encoding.Unicode.GetString(srv, i + k + 4, num2 * 2);

						dictionary[num] = value;

						num++;

					}

					catch

					{

						continue;

					}

					break;

				}

			}

		}

		Dictionary<string, string> dictionary2 = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

		dictionary2.Add("Poland", "Polska");

		dictionary2.Add("Italy", "Włochy");

		dictionary2.Add("Spain", "Hiszpania");

		dictionary2.Add("Germany", "Niemcy");

		dictionary2.Add("France", "Francja");

		dictionary2.Add("England", "Anglia");

		dictionary2.Add("Brazil", "Brazylia");

		dictionary2.Add("Argentina", "Argentyna");

		dictionary2.Add("Portugal", "Portugalia");

		dictionary2.Add("Netherlands", "Holandia");

		dictionary2.Add("Belgium", "Belgia");

		dictionary2.Add("Czech Republic", "Czechy");

		dictionary2.Add("Croatia", "Chorwacja");

		dictionary2.Add("Serbia", "Serbia");

		dictionary2.Add("Sweden", "Szwecja");

		dictionary2.Add("Norway", "Norwegia");

		dictionary2.Add("Denmark", "Dania");

		dictionary2.Add("Greece", "Grecja");

		dictionary2.Add("Turkey", "Turcja");

		dictionary2.Add("Russia", "Rosja");

		dictionary2.Add("Ukraine", "Ukraina");

		dictionary2.Add("Austria", "Austria");

		dictionary2.Add("Switzerland", "Szwajcaria");

		dictionary2.Add("Cameroon", "Kamerun");

		dictionary2.Add("Nigeria", "Nigeria");

		dictionary2.Add("Ivory Coast", "WKS");

		dictionary2.Add("Ghana", "Ghana");

		dictionary2.Add("Senegal", "Senegal");

		dictionary2.Add("Egypt", "Egipt");

		dictionary2.Add("Morocco", "Maroko");

		dictionary2.Add("Colombia", "Kolumbia");

		dictionary2.Add("Uruguay", "Urugwaj");

		dictionary2.Add("Chile", "Chile");

		dictionary2.Add("Paraguay", "Paragwaj");

		dictionary2.Add("Mexico", "Meksyk");

		dictionary2.Add("United States", "USA");

		dictionary2.Add("Japan", "Japonia");

		dictionary2.Add("South Korea", "Korea Płd.");

		dictionary2.Add("Australia", "Australia");

		dictionary2.Add("Scotland", "Szkocja");

		dictionary2.Add("Wales", "Walia");

		dictionary2.Add("Northern Ireland", "Irlandia Płn.");

		dictionary2.Add("Republic of Ireland", "Irlandia");

		dictionary2.Add("Slovakia", "Słowacja");

		dictionary2.Add("Slovenia", "Słowenia");

		dictionary2.Add("Bosnia & Herzegovina", "Bośnia i Herc.");

		dictionary2.Add("Romania", "Rumunia");

		dictionary2.Add("Bulgaria", "Bułgaria");

		dictionary2.Add("Hungary", "Węgry");

		dictionary2.Add("Finland", "Finlandia");

		dictionary2.Add("Iceland", "Islandia");

		Dictionary<string, string> dictionary3 = dictionary2;

		Dictionary<int, string> dictionary4 = new Dictionary<int, string>();

		foreach (KeyValuePair<int, string> item in dictionary)

		{

			string value2;

			if (dictionary3.TryGetValue(item.Value, out value2))

			{

				dictionary4[item.Key] = value2;

			}

			else

			{

				dictionary4[item.Key] = item.Value;

			}

		}

		return dictionary4;

	}



	private static string GetSidesString(bool l, bool c, bool r)

	{

		if (r && l && c)

		{

			return "RLC";

		}

		if (l && c)

		{

			return "LC";

		}

		if (r && c)

		{

			return "RC";

		}

		if (r && l)

		{

			return "RL";

		}

		if (r)

		{

			return "R";

		}

		if (l)

		{

			return "L";

		}

		if (c)

		{

			return "C";

		}

		return "";

	}



	private static void AddPositionsToFormat(List<string> parts, int threshold, byte gk, byte sw, byte dl, byte dc, byte dr, byte dm, byte ml, byte mc, byte mr, byte aml, byte amc, byte amr, byte st, byte wbl, byte wbr)

	{

		if (gk >= threshold)

		{

			parts.Add("GK");

		}

		if (sw >= threshold)

		{

			parts.Add("SW");

		}

		string sidesString = GetSidesString(dl >= threshold, dc >= threshold, dr >= threshold);

		if (!string.IsNullOrEmpty(sidesString))

		{

			parts.Add("D (" + sidesString + ")");

		}

		string sidesString2 = GetSidesString(wbl >= threshold, false, wbr >= threshold);

		if (!string.IsNullOrEmpty(sidesString2))

		{

			parts.Add("WB (" + sidesString2 + ")");

		}

		if (dm >= threshold)

		{

			parts.Add("DM");

		}

		string sidesString3 = GetSidesString(ml >= threshold, mc >= threshold, mr >= threshold);

		if (!string.IsNullOrEmpty(sidesString3))

		{

			parts.Add("M (" + sidesString3 + ")");

		}

		string sidesString4 = GetSidesString(aml >= threshold, amc >= threshold, amr >= threshold);

		if (!string.IsNullOrEmpty(sidesString4))

		{

			parts.Add("AM (" + sidesString4 + ")");

		}

		if (st >= threshold)

		{

			parts.Add("ST");

		}

	}



	public static string FormatPosition(byte gk, byte sw, byte dl, byte dc, byte dr, byte dm, byte ml, byte mc, byte mr, byte aml, byte amc, byte amr, byte st, byte wbl, byte wbr)

	{

		if (gk >= 15)

		{

			return "GK";

		}

		List<string> list = new List<string>();

		AddPositionsToFormat(list, 15, gk, sw, dl, dc, dr, dm, ml, mc, mr, aml, amc, amr, st, wbl, wbr);

		if (list.Count == 0)

		{

			AddPositionsToFormat(list, 10, gk, sw, dl, dc, dr, dm, ml, mc, mr, aml, amc, amr, st, wbl, wbr);

		}

		if (list.Count == 0)

		{

			byte b16 = Math.Max(gk, Math.Max(sw, Math.Max(dl, Math.Max(dc, Math.Max(dr, Math.Max(dm, Math.Max(ml, Math.Max(mc, Math.Max(mr, Math.Max(aml, Math.Max(amc, Math.Max(amr, Math.Max(st, Math.Max(wbl, wbr))))))))))))));

			if (b16 > 1)

			{

				AddPositionsToFormat(list, b16, gk, sw, dl, dc, dr, dm, ml, mc, mr, aml, amc, amr, st, wbl, wbr);

			}

		}

		return (list.Count > 0) ? string.Join(", ", list.ToArray()) : "-";

	}



	private static string FormatPosition(byte[] row)

	{

		return FormatPosition(row[9], row[10], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28], row[29], row[30], row[31], row[32], row[33]);

	}



	private static int FindNameTableStart(byte[] srv, int startSearch, int endSearch)

	{

		if (endSearch > srv.Length - 1000)

		{

			endSearch = srv.Length - 1000;

		}

		for (int i = startSearch; i < endSearch; i++)

		{

			if (srv[i] != 1 || srv[i + 1] != 0 || srv[i + 2] != 0 || srv[i + 3] != 0 || srv[i + 8] != 0)

			{

				continue;

			}

			int num = BitConverter.ToInt32(srv, i + 9);

			if (num < 1 || num > 120)

			{

				continue;

			}

			int num2 = i + 22 + num * 2;

			if (num2 + 25 >= srv.Length || BitConverter.ToInt32(srv, num2) != 2 || srv[num2 + 8] != 0)

			{

				continue;

			}

			int num3 = BitConverter.ToInt32(srv, num2 + 9);

			if (num3 >= 1 && num3 <= 120)

			{

				int num4 = num2 + 22 + num3 * 2;

				if (num4 + 25 < srv.Length && BitConverter.ToInt32(srv, num4) == 3 && srv[num4 + 8] == 0)

				{

					return i;

				}

			}

		}

		return -1;

	}



	private static Dictionary<int, string> ParseNativeNames(byte[] srv, int anchor, Dictionary<int, string> cache, Dictionary<string, int> reverse, out int end)
	{
		int start = -1;
		for (int candidate = Math.Max(0, anchor - 2048); candidate <= anchor; candidate++)
		{
			int count = BitConverter.ToInt32(srv, candidate);
			if (count < 3 || count > 1000000) continue;
			int position = candidate + 4;
			bool valid = true;
			for (int index = 0; index < 3; index++)
			{
				if (position + 5 > srv.Length || srv[position] != 0) { valid = false; break; }
				int length = BitConverter.ToInt32(srv, position + 1);
				long footer = position + 14L + length * 2L;
				if (length < 1 || length > 150 || footer + 8 > srv.Length || BitConverter.ToInt32(srv, (int)footer) != index) { valid = false; break; }
				position = (int)footer + 8;
			}
			if (valid) { start = candidate; break; }
		}
		if (start < 0) throw new InvalidDataException("Native name table was not found.");
		var result = new Dictionary<int, string>();
		int total = BitConverter.ToInt32(srv, start);
		end = start + 4;
		if (cache != null) cache.Clear();
		if (reverse != null) reverse.Clear();
		for (int index = 0; index < total; index++)
		{
			if (end + 5 > srv.Length || srv[end] != 0) throw new InvalidDataException("Invalid native name record.");
			int length = BitConverter.ToInt32(srv, end + 1);
			long footer = end + 14L + length * 2L;
			if (length < 1 || length > 150 || footer + 8 > srv.Length || BitConverter.ToInt32(srv, (int)footer) != index)
				throw new InvalidDataException("Invalid native name footer.");
			string name = Encoding.Unicode.GetString(srv, end + 5, length * 2);
			result[index - 1] = name;
			if (cache != null) cache[index - 1] = name;
			if (reverse != null && !reverse.ContainsKey(name)) reverse[name] = index - 1;
			end = (int)footer + 8;
		}
		return result;
	}

	private static Dictionary<int, string> ParseFirstNames(byte[] srv, out int fnStart, out int snStart)

	{

		fnStart = FindNameTableStart(srv, 5000000, srv.Length - 1000);

		if (fnStart < 0)

		{

			fnStart = 9514715;

		}

		snStart = FindNameTableStart(srv, fnStart + 100000, srv.Length - 1000);

		if (snStart < 0)

		{

			snStart = 12610801;

		}

		int end;
		return ParseNativeNames(srv, fnStart, FirstNamesDict, FirstNamesRev, out end);

	}



	private static Dictionary<int, string> ParseSurnames(byte[] srv, int snStart, out Dictionary<int, string> surnamesByPid, out int cnStart)

	{

		surnamesByPid = new Dictionary<int, string>();

		cnStart = FindNameTableStart(srv, snStart + 100000, srv.Length - 1000);

		int end;
		return ParseNativeNames(srv, snStart, SurnamesDict, SurnamesRev, out end);

	}



	private static Dictionary<int, string> ParseCommonNames(byte[] srv, int cnStart)

	{

		if (cnStart < 0) return new Dictionary<int, string>();
		int end;
		return ParseNativeNames(srv, cnStart, null, CommonNamesRev, out end);

	}



	private static Dictionary<int, string[]> ParseEntityTreeAndTags(byte[] srv)

	{

		Dictionary<int, string[]> dictionary = new Dictionary<int, string[]>();

		for (int i = 900000; i < 4000000 && i < srv.Length - 60; i++)

		{

			for (int j = 6; j <= 12; j += 2)

			{

				int num = BitConverter.ToInt32(srv, i + j);

				if (num < 1 || num > 30)

				{

					continue;

				}

				int num2 = i + j + 4 + num * 2;

				if (num2 + 6 >= srv.Length || srv[num2] != 0 || srv[num2 + 1] != 0)

				{

					continue;

				}

				int num3 = BitConverter.ToInt32(srv, num2 + 2);

				if (num3 < 1 || num3 > 35)

				{

					continue;

				}

				int num4 = num2 + 6 + num3 * 2;

				if (num4 + 2 > srv.Length || srv[num4] != 0 || srv[num4 + 1] != 0)

				{

					continue;

				}

				string text = Encoding.Unicode.GetString(srv, i + j + 4, num * 2);

				string text2 = Encoding.Unicode.GetString(srv, num2 + 6, num3 * 2);

				bool flag = true;

				string text3 = text;

				foreach (char c in text3)

				{

					if (c < ' ' || c > 'ɘ')

					{

						flag = false;

						break;

					}

				}

				text3 = text2;

				foreach (char c in text3)

				{

					if (c < ' ' || c > 'ɘ')

					{

						flag = false;

						break;

					}

				}

				if (flag)

				{

					int num5 = BitConverter.ToInt32(srv, i);

					if (num5 > 0 && !dictionary.ContainsKey(num5))

					{

						dictionary[num5] = new string[2] { text, text2 };

					}

				}

			}

		}

		byte[] array = new byte[4] { 100, 105, 116, 115 };

		byte[] array2 = new byte[4] { 109, 110, 116, 115 };

		for (int i = 0; i <= srv.Length - 30; i++)

		{

			if (srv[i] != array[0] || srv[i + 1] != array[1] || srv[i + 2] != array[2] || srv[i + 3] != array[3])

			{

				continue;

			}

			for (int l = i + 5; l <= i + 15 && l <= srv.Length - 10; l++)

			{

				if (srv[l] != array2[0] || srv[l + 1] != array2[1] || srv[l + 2] != array2[2] || srv[l + 3] != array2[3])

				{

					continue;

				}

				int num6 = BitConverter.ToInt32(srv, i + 5);

				int num7 = BitConverter.ToInt32(srv, l + 5);

				if (num6 <= 0 || num7 <= 0 || num7 >= 50 || l + 9 + num7 * 2 > srv.Length)

				{

					continue;

				}

				string text4 = Encoding.Unicode.GetString(srv, l + 9, num7 * 2);

				if (!SrvNameOffsetsByPid.ContainsKey(num6))

				{

					SrvNameOffsetsByPid[num6] = l + 5;

				}

				bool flag2 = true;

				string text3 = text4;

				foreach (char c in text3)

				{

					if (c < ' ' || c > 'ɘ')

					{

						flag2 = false;

						break;

					}

				}

				if (flag2 && !dictionary.ContainsKey(num6))

				{

					int num8 = text4.LastIndexOf(' ');

					if (num8 > 0)

					{

						dictionary[num6] = new string[2]

						{

							text4.Substring(0, num8),

							text4.Substring(num8 + 1)

						};

					}

					else

					{

						dictionary[num6] = new string[2] { "", text4 };

					}

				}

			}

		}

		return dictionary;

	}



	private static Dictionary<int, PersonDetails> ParsePersonData(byte[] ppl, Dictionary<int, string> firstNames, Dictionary<int, string> surnames, Dictionary<int, string> commonNames, Dictionary<int, string> clubs)

	{

		Dictionary<int, PersonDetails> dictionary = new Dictionary<int, PersonDetails>();
		int attributeStart = Find89ByteTable(ppl) - 81;
		int personEnd = attributeStart - 8 - BitConverter.ToInt32(ppl, 4) * 17;
		int personCount = BitConverter.ToInt32(ppl, 0);
		for (int i = 20; i <= personEnd - 219; i++)

		{

			if (ppl[i + 11] != 108 || ppl[i + 12] != 7 || ppl[i + 13] != 16 || ppl[i + 14] != 39)

			{

				continue;

			}

			int recordStart = i - 15;
			int personIndex = BitConverter.ToInt32(ppl, recordStart);
			if (ppl[recordStart + 4] != 2 || personIndex < 0 || personIndex >= personCount) continue;
			int recordEnd = -1;
			for (int footer = recordStart + 200; footer <= Math.Min(personEnd - 8, recordStart + 4096); footer++)
			{
				if (BitConverter.ToInt32(ppl, footer) != personIndex || BitConverter.ToInt32(ppl, footer + 4) <= 0) continue;
				int next = footer + 8;
				if (next == personEnd || (next + 5 <= personEnd && BitConverter.ToInt32(ppl, next) >= 0 && BitConverter.ToInt32(ppl, next) < personCount && ppl[next + 4] >= 1 && ppl[next + 4] <= 5))
				{
					recordEnd = next;
					break;
				}
			}
			if (recordEnd < 0) continue;

			int num = BitConverter.ToInt32(ppl, i);

			short num2 = BitConverter.ToInt16(ppl, i - 2);

			short num3 = BitConverter.ToInt16(ppl, i - 4);

			short num4 = BitConverter.ToInt16(ppl, i - 10);

			short num5 = BitConverter.ToInt16(ppl, i - 8);

			short num6 = BitConverter.ToInt16(ppl, i - 6);

			short num7 = BitConverter.ToInt16(ppl, i + 25);

			short num8 = BitConverter.ToInt16(ppl, i + 27);

			if (num8 < 0 && num8 >= -250)

			{

				num8 = Math.Abs(num8);

			}

			if (num7 < 0 && num7 >= -200)

			{

				num7 = Math.Abs(num7);

			}

			if (num < 0 || num >= 500000 || num2 < -10 || num2 > 200 || num3 < 0 || num3 > 200)

			{

				continue;

			}

			string text = "";

			string text2 = "";

			string commonName = "";

			int fnIdOff = 0;

			int snIdOff = 0;

			int cnIdOff = 0;

			for (int j = i + 80; j <= i + 520 && j + 22 < recordEnd - 8; j++)

			{

				if (ppl[j] != 108 || ppl[j + 1] != 7 || ppl[j + 2] != byte.MaxValue || ppl[j + 3] != byte.MaxValue || ppl[j + 4] != byte.MaxValue || ppl[j + 5] != byte.MaxValue)

				{

					continue;

				}

				int num9 = BitConverter.ToInt32(ppl, j + 6);

				int num10 = BitConverter.ToInt32(ppl, j + 10);

				int num11 = BitConverter.ToInt32(ppl, j + 14);

				string text3 = "";

				string text4 = "";

				bool flag = false;

				int num12 = BitConverter.ToInt32(ppl, j + 18);

				if (num12 >= 2 && num12 <= 45 && j + 22 + num12 * 2 <= ppl.Length)

				{

					string text5 = Encoding.Unicode.GetString(ppl, j + 22, num12 * 2);

					bool flag2 = true;

					string text6 = text5;

					foreach (char c in text6)

					{

						if (c < ' ' || c > 'ɘ')

						{

							flag2 = false;

							break;

						}

					}

					if (flag2 && text5.Length >= 2)

					{

						flag = true;

						int num13 = text5.IndexOf(' ');

						if (num13 > 0)

						{

							text3 = text5.Substring(0, num13).Trim();

							text4 = text5.Substring(num13 + 1).Trim();

						}

						else

						{

							text4 = text5.Trim();

						}

					}

				}

				bool flag3 = num9 >= 0 && firstNames.ContainsKey(num9 - 1);

				bool flag4 = num10 >= 0 && surnames.ContainsKey(num10 - 1);

				bool flag5 = num11 >= 0 && commonNames.ContainsKey(num11 - 1);

				if (!flag && !flag3 && !flag4 && !flag5)

				{

					continue;

				}

				fnIdOff = j + 6;

				snIdOff = j + 10;

				cnIdOff = j + 14;

				if (string.IsNullOrEmpty(text4) && flag4)

				{

					if (surnames.ContainsKey(num10 - 1))

					{

						text4 = surnames[num10 - 1];

					}

					else if (surnames.ContainsKey(num10))

					{

						text4 = surnames[num10];

					}

				}

				if (string.IsNullOrEmpty(text3) && flag3)

				{

					if (firstNames.ContainsKey(num9 - 1))

					{

						text3 = firstNames[num9 - 1];

					}

					else if (firstNames.ContainsKey(num9))

					{

						text3 = firstNames[num9];

					}

				}

				string text7 = "";

				if (flag5)

				{

					if (commonNames.ContainsKey(num11 - 1))

					{

						text7 = commonNames[num11 - 1];

					}

					else if (commonNames.ContainsKey(num11))

					{

						text7 = commonNames[num11];

					}

				}

				if (!string.IsNullOrEmpty(text7))

				{

					commonName = text7;

				}

				if (!string.IsNullOrEmpty(text7))

				{

					if (string.IsNullOrEmpty(text4) && string.IsNullOrEmpty(text3))

					{

						int num13 = text7.IndexOf(' ');

						if (num13 > 0)

						{

							text3 = text7.Substring(0, num13).Trim();

							text4 = text7.Substring(num13 + 1).Trim();

						}

						else

						{

							text4 = text7;

						}

					}

					else if (string.IsNullOrEmpty(text4))

					{

						int num13 = text3.IndexOf(' ');

						if (num13 > 0)

						{

							text4 = text3.Substring(num13 + 1).Trim();

							text3 = text3.Substring(0, num13).Trim();

						}

						else

						{

							text4 = text7;

						}

					}

					else if (!text4.Equals(text7, StringComparison.OrdinalIgnoreCase) && !text4.Contains(text7))

					{

						text4 = text4 + " (" + text7 + ")";

					}

				}

				else if (string.IsNullOrEmpty(text4) && !string.IsNullOrEmpty(text3))

				{

					int num13 = text3.IndexOf(' ');

					if (num13 > 0)

					{

						text4 = text3.Substring(num13 + 1).Trim();

						text3 = text3.Substring(0, num13).Trim();

					}

				}

				if (!string.IsNullOrEmpty(text4) && !string.IsNullOrEmpty(text3))

				{

					text = text3;

					text2 = text4;

					break;

				}

				if (!string.IsNullOrEmpty(text4) && string.IsNullOrEmpty(text2))

				{

					text2 = text4;

					if (!string.IsNullOrEmpty(text3))

					{

						text = text3;

					}

				}

				else if (!string.IsNullOrEmpty(text3) && string.IsNullOrEmpty(text))

				{

					text = text3;

				}

			}

			if (string.IsNullOrEmpty(text2) || string.IsNullOrEmpty(text))

			{

				for (int l = i + 80; l <= i + 520 && l + 16 < recordEnd - 8; l++)

				{

					if (ppl[l] != byte.MaxValue || ppl[l + 1] != byte.MaxValue || ppl[l + 2] != byte.MaxValue || ppl[l + 3] != byte.MaxValue)

					{

						continue;

					}

					int key = BitConverter.ToInt32(ppl, l + 4) - 1;

					int key2 = BitConverter.ToInt32(ppl, l + 8) - 1;

					if (surnames.ContainsKey(key2) && firstNames.ContainsKey(key))

					{

						text = firstNames[key];

						text2 = surnames[key2];

						break;

					}

					if (l + 14 <= ppl.Length && ppl[l + 4] == 0 && ppl[l + 5] == 0)

					{

						int key3 = BitConverter.ToInt32(ppl, l + 6) - 1;

						int key4 = BitConverter.ToInt32(ppl, l + 10) - 1;

						if (surnames.ContainsKey(key4) && firstNames.ContainsKey(key3))

						{

							text = firstNames[key3];

							text2 = surnames[key4];

							break;

						}

					}

				}

			}

			int num14 = 0;

			short num15 = 0;

			int clubIdOff = 0;

			for (int l = i + 140; l <= i + 230 && l + 8 < recordEnd - 8; l++)

			{

				if (ppl[l] != 108 || ppl[l + 1] != 7 || ppl[l - 1] != 0 || ppl[l - 2] != 0)

				{

					continue;

				}

				short num16 = BitConverter.ToInt16(ppl, l + 2);

				if (num16 > 0 && ppl[l + 4] == 0 && ppl[l + 5] == 0)

				{

					if (num15 == 0)

					{

						num15 = num16;

						clubIdOff = l + 2;

					}

					if (ppl[l + 6] == 1)

					{

						num14 = num16;

						clubIdOff = l + 2;

						break;

					}

				}

			}

			if (num14 == 0)

			{

				num14 = num15;

			}

			if (num14 == 0)

			{

				short num17 = BitConverter.ToInt16(ppl, i + 227);

				if (i + 229 < recordEnd - 8 && num17 > 0 && clubs.ContainsKey(num17))

				{

					num14 = num17;

				}

			}

			DateTime? dateTime = null;

			int num18 = 0;

			int nationId = 0;

			int num19 = -1;

			int bDateOff = 0;

			for (int l = i + 80; l <= i + 350 && l + 16 < recordEnd - 8; l++)

			{

				ushort num20 = BitConverter.ToUInt16(ppl, l);

				if (num20 < 1950 || num20 > 1995)

				{

					continue;

				}

				ushort num21 = BitConverter.ToUInt16(ppl, l - 2);

				if (num21 >= 366)

				{

					continue;

				}

				int num22 = BitConverter.ToInt32(ppl, l + 5);

				if (num22 < 0 || num22 > 300)

				{

					continue;

				}

				try

				{

					dateTime = new DateTime(num20, 1, 1).AddDays((int)num21);

					bDateOff = l;

					num19 = l - 2;

					nationId = num22;

					num18 = 2007 - num20;

					if (dateTime > new DateTime(2007, 7, 1))

					{

						num18--;

					}

				}

				catch

				{

					continue;

				}

				break;

			}

			DateTime? contractExpires = null;

			int contractExpOff = 0;

			int verifiedClub = FindNativePersonClubOffset(ppl, recordStart, recordEnd - 8, personIndex,
				bDateOff > 0 ? bDateOff + 5 : 0, clubIdOff);
			if (verifiedClub > 0)
			{
				clubIdOff = verifiedClub;
				num14 = BitConverter.ToInt32(ppl, verifiedClub);
			}
			int verifiedFreeClub = FindNativeFreePlayerClubOffset(ppl, recordStart, recordEnd - 8,
				bDateOff > 0 ? bDateOff + 5 : 0);
			if (verifiedFreeClub > 0)
			{
				if (verifiedClub > 0)
					throw new InvalidDataException("Conflicting free/contracted ownership for person index " + personIndex);
				clubIdOff = verifiedFreeClub;
				num14 = 0;
			}

			int nativeContract = clubIdOff + 28;
			int nativeLength = clubIdOff > 0 ? GetNativeContractLength(ppl, nativeContract, recordEnd - 8, personIndex) : 0;
			int payload = nativeLength > 0 ? GetNativeClubContractOffset(ppl, nativeContract, recordEnd - 8, personIndex) : -1;
			int weeklyWage = 0;
			byte squadNumber = 0;
			if (payload >= 0)
			{
				contractExpOff = payload + 41;
				ushort year = BitConverter.ToUInt16(ppl, contractExpOff);
				ushort day = BitConverter.ToUInt16(ppl, payload + 39);
				if (year >= 1900 && year <= 9999 && day < (DateTime.IsLeapYear(year) ? 366 : 365))
				{
					if (year != 1900 || day != 0) contractExpires = new DateTime(year, 1, 1).AddDays(day);
				}
				else throw new InvalidDataException("Invalid native contract expiry for person index " + personIndex);
				weeklyWage = BitConverter.ToInt32(ppl, payload + 35);
				squadNumber = ppl[payload + 60];
			}

			if (nativeLength < 0 && num19 > 0)

			{

				for (int m = num19 + 60; m <= num19 + 160 && m + 8 < recordEnd - 8; m++)

				{

					ushort num23 = BitConverter.ToUInt16(ppl, m);

					if (num23 < 2007 || num23 > 2025)

					{

						continue;

					}

					ushort num24 = BitConverter.ToUInt16(ppl, m - 2);

					if (num24 < 366)

					{

						try

						{

							contractExpires = new DateTime(num23, 1, 1).AddDays((int)num24);

							contractExpOff = m;

						}

						catch

						{

							continue;

						}

						break;

					}

				}

			}

			dictionary[num] = new PersonDetails

			{
				UniqueId = BitConverter.ToInt32(ppl, recordEnd - 4),

				PersonOffset = i,

				CA = num3,

				PA = num2,

				CurrentReputation = ((num4 >= 0 && num4 <= 200) ? num4 : 0),

				HomeReputation = ((num5 >= 0 && num5 <= 200) ? num5 : 0),

				WorldReputation = ((num6 >= 0 && num6 <= 200) ? num6 : 0),

				Height = ((num8 >= 140 && num8 <= 220) ? num8 : 0),

				Weight = ((num7 >= 40 && num7 <= 130) ? num7 : 0),

				ClubId = num14,

				FirstName = text,

				LastName = text2,

				CommonName = commonName,

				BirthDate = dateTime,

				Age = num18,

				NationId = nationId,

				ContractExpires = contractExpires,

				FirstNameIdOffset = fnIdOff,

				LastNameIdOffset = snIdOff,

				CommonNameIdOffset = cnIdOff,

				BirthDateOffset = bDateOff,

				ContractExpiresOffset = contractExpOff,

				WeeklyWage = weeklyWage,

				SquadNumber = squadNumber,
				ClubIdOffset = verifiedFreeClub > 0 ? 0 : clubIdOff,

				NationIdOffset = (bDateOff > 0 ? bDateOff + 5 : 0)

			};

		}

		return dictionary;

	}



	private static int Find89ByteTable(byte[] ppl)

	{

		int count = ppl.Length >= 12 ? BitConverter.ToInt32(ppl, 8) : -1;
		int start = Math.Max(0, Math.Min(100000000, ppl.Length - 356));
		for (int i = start; i < ppl.Length - 356; i++)

		{

			if (BitConverter.ToInt32(ppl, i) == 0 && BitConverter.ToInt32(ppl, i + 89) == 1 && BitConverter.ToInt32(ppl, i + 178) == 2 && BitConverter.ToInt32(ppl, i + 267) == 3 &&
				(count <= 0 || (i >= 85 && BitConverter.ToInt32(ppl, i - 85) == count)))

			{

				return i;

			}

		}

		return 102005633;

	}



	

	private static int FindRetirementTable(byte[] srv)
	{
		if (srv == null) return -1;
		byte[] signature = { 0x24, 0x00, 0xD8, 0x07, 0x6D, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF };
		int found = -1;
		for (int position = 0; position <= srv.Length - 17; position++)
		{
			if (srv[position] != signature[0]) continue;
			bool matches = true;
			for (int index = 1; index < signature.Length; index++)
			{
				if (srv[position + index] != signature[index]) { matches = false; break; }
			}
			if (!matches) continue;
			int count = BitConverter.ToInt32(srv, position + 12);
			if (count < 0 || position + 17L + count * 18L > srv.Length || srv[position + 16] > 1)
				throw new InvalidDataException("Invalid retirement table header.");
			if (found >= 0) throw new InvalidDataException("Ambiguous retirement table header.");
			found = position;
		}
		return found;
	}

	public static Dictionary<int, DateTime> ParseRetirements(byte[] srv)

	{

		var dict = new Dictionary<int, DateTime>();

		int tablePosition = FindRetirementTable(srv);
		if (tablePosition < 0) return dict;

		byte[] sig = new byte[] { 0x24, 0x00, 0xD8, 0x07, 0x6D, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF };

		int sigPos = -1;

		for (int i = tablePosition; i < srv.Length - sig.Length; i++)

		{

			bool match = true;

			for (int j = 0; j < sig.Length; j++)

			{

				if (srv[i + j] != sig[j]) { match = false; break; }

			}

			if (match) { sigPos = i; break; }

		}

		if (sigPos == -1) return dict;



		int countPos = sigPos + sig.Length;

		int count = BitConverter.ToInt32(srv, countPos);

		int startPos = countPos + 5;



		for (int i = 0; i < count; i++)

		{

			int off = startPos + i * 18;

			if (off + 18 > srv.Length) throw new InvalidDataException("Truncated retirement record.");

			int pid = BitConverter.ToInt32(srv, off);

			short doy = BitConverter.ToInt16(srv, off + 4);

			short year = BitConverter.ToInt16(srv, off + 6);

			if (pid > 0 && srv[off + 8] == 1 && year >= 1900 && year <= 2100 && doy >= 0 && doy < (DateTime.IsLeapYear(year) ? 366 : 365))

			{

				try { dict[pid] = new DateTime(year, 1, 1).AddDays(doy); } catch { }

			}

		}

		return dict;

	}



	public sealed class NativeLoanRecord
	{
		public int PersonIndex;
		public int ClubId;
		public int RecordIndex;
		public int UniqueId;
		public DateTime StartDate;
		public DateTime EndDate;
		// Keep these as raw values until controlled one-field SI variants prove the flags/sentinels.
		public byte OptionsRaw;
		public bool CanBeRecalled { get { return (OptionsRaw & 0x04) != 0; } }
		public byte SquadNumberRaw;
		public int FeeToBuyRaw;
		public byte WageContributionRaw;
	}

	private static int FindNativeLoanTable(byte[] server, int personCount)
	{
		if (server == null || personCount <= 0)
			throw new InvalidDataException("Invalid database for native loans.");
		int found = -1;
		for (int header = 0; header + 36 <= server.Length; header++)
		{
			int count = BitConverter.ToInt32(server, header);
			// Original loans use UID -1; newly created SI loans can have a positive entity UID.
			if (count <= 0 || count > personCount || (long)header + 4 + (long)count * 32 > server.Length ||
				server[header + 4] != 0 || BitConverter.ToInt32(server, header + 28) != 0 ||
				BitConverter.ToInt32(server, header + 32) == 0 || BitConverter.ToInt32(server, header + 32) < -1) continue;
			bool valid = true;
			var uniqueLoanIds = new HashSet<int>();
			for (int index = 0; index < count; index++)
			{
				int row = header + 4 + index * 32;
				int loanUid = BitConverter.ToInt32(server, row + 28);
				int person = BitConverter.ToInt32(server, row + 1);
				int club = BitConverter.ToInt32(server, row + 5);
				int startYear = BitConverter.ToUInt16(server, row + 11);
				int endYear = BitConverter.ToUInt16(server, row + 15);
				if (server[row] != 0 || person < -1 || person >= personCount || club < -1 ||
					startYear < 1900 || startYear > 2100 || endYear < 1900 || endYear > 2100 ||
					BitConverter.ToUInt16(server, row + 9) >= (DateTime.IsLeapYear(startYear) ? 366 : 365) ||
					BitConverter.ToUInt16(server, row + 13) >= (DateTime.IsLeapYear(endYear) ? 366 : 365) ||
					BitConverter.ToInt32(server, row + 24) != index || loanUid == 0 || loanUid < -1 ||
						(loanUid > 0 && !uniqueLoanIds.Add(loanUid)))
				{
					valid = false;
					break;
				}
			}
			if (!valid) continue;
			if (found >= 0) throw new InvalidDataException("Ambiguous native loan table.");
			found = header;
		}
		if (found < 0) throw new InvalidDataException("Unsupported or missing native loan table.");
		return found;
	}

	public static List<NativeLoanRecord> ParseNativeLoans(byte[] server, int personCount)
	{
		int header = FindNativeLoanTable(server, personCount);
		int count = BitConverter.ToInt32(server, header);
		var loans = new List<NativeLoanRecord>();
		for (int index = 0; index < count; index++)
		{
			int row = header + 4 + index * 32;
			loans.Add(new NativeLoanRecord {
				PersonIndex = BitConverter.ToInt32(server, row + 1),
				ClubId = BitConverter.ToInt32(server, row + 5),
				RecordIndex = BitConverter.ToInt32(server, row + 24),
				UniqueId = BitConverter.ToInt32(server, row + 28),
				StartDate = new DateTime(BitConverter.ToUInt16(server, row + 11), 1, 1).AddDays(BitConverter.ToUInt16(server, row + 9)),
				EndDate = new DateTime(BitConverter.ToUInt16(server, row + 15), 1, 1).AddDays(BitConverter.ToUInt16(server, row + 13)),
				OptionsRaw = server[row + 17],
				SquadNumberRaw = server[row + 18],
				FeeToBuyRaw = BitConverter.ToInt32(server, row + 19),
				WageContributionRaw = server[row + 23]
			});
		}
		return loans;
	}

	public static byte[] RemoveNativeLoans(byte[] server, int personCount, HashSet<int> personIndices)
	{
		if (personIndices == null) throw new ArgumentNullException("personIndices");
		foreach (int index in personIndices)
			if (index < 0 || index >= personCount) throw new InvalidDataException("Invalid loan player index.");
		int header = FindNativeLoanTable(server, personCount);
		int count = BitConverter.ToInt32(server, header);
		int retained = 0;
		for (int index = 0; index < count; index++)
			if (!personIndices.Contains(BitConverter.ToInt32(server, header + 5 + index * 32))) retained++;
		if (retained == count) return server;
		byte[] updated = new byte[server.Length - (count - retained) * 32];
		Buffer.BlockCopy(server, 0, updated, 0, header);
		BitConverter.GetBytes(retained).CopyTo(updated, header);
		int next = 0;
		for (int index = 0; index < count; index++)
		{
			int row = header + 4 + index * 32;
			if (personIndices.Contains(BitConverter.ToInt32(server, row + 1))) continue;
			int destination = header + 4 + next * 32;
			Buffer.BlockCopy(server, row, updated, destination, 32);
			BitConverter.GetBytes(next++).CopyTo(updated, destination + 24);
		}
		int end = header + 4 + count * 32;
		Buffer.BlockCopy(server, end, updated, header + 4 + retained * 32, server.Length - end);
		return updated;
	}

	public static byte[] SyncRetirements(byte[] srv, List<PlayerRecord> players)

	{

		if (srv == null || players == null) return srv;
		int tablePosition = FindRetirementTable(srv);
		if (tablePosition < 0) throw new InvalidDataException("Retirement table was not found. The database was not changed.");
		srv = (byte[])srv.Clone();

		byte[] sig = new byte[] { 0x24, 0x00, 0xD8, 0x07, 0x6D, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF };

		int sigPos = -1;

		for (int i = tablePosition; i < srv.Length - sig.Length; i++)

		{

			bool match = true;

			for (int j = 0; j < sig.Length; j++)

			{

				if (srv[i + j] != sig[j]) { match = false; break; }

			}

			if (match) { sigPos = i; break; }

		}

		if (sigPos == -1) return srv;



		int countPos = sigPos + sig.Length;

		int currentCount = BitConverter.ToInt32(srv, countPos);

		int startPos = countPos + 5;



		Dictionary<int, int> existing = new Dictionary<int, int>();

		for (int i = 0; i < currentCount; i++)

		{

			int off = startPos + i * 18;

			if (off + 4 > srv.Length) break;

			int pid = BitConverter.ToInt32(srv, off);

			existing[pid] = i;

		}



		List<PlayerRecord> toAdd = new List<PlayerRecord>();

		foreach (var p in players)

		{
			if (p.Id <= 0) throw new InvalidDataException("Invalid player identity for retirement.");
			if (!p.RetirementDate.HasValue)
			{
				int existingIndex;
				if (existing.TryGetValue(p.Id, out existingIndex)) srv[startPos + existingIndex * 18 + 8] = 0;
				continue;
			}
			if (p.RetirementDate.Value.Year < 1900 || p.RetirementDate.Value.Year > 2100)
				throw new InvalidDataException("Retirement year must be between 1900 and 2100.");

			if (p.RetirementDate.HasValue)

			{

				ushort doy = (ushort)(p.RetirementDate.Value.DayOfYear - 1);

				ushort yr = (ushort)p.RetirementDate.Value.Year;

				if (existing.ContainsKey(p.Id))

				{

					int off = startPos + existing[p.Id] * 18;

					BitConverter.GetBytes(doy).CopyTo(srv, off + 4);

					BitConverter.GetBytes(yr).CopyTo(srv, off + 6);

					srv[off + 8] = 0x01;

				}

				else

				{

					toAdd.Add(p);

				}

			}

		}



		if (toAdd.Count == 0) return srv;



		int tableEndPos = startPos + currentCount * 18;

		int newCount = currentCount + toAdd.Count;

		int bytesToInsert = toAdd.Count * 18;



		byte[] newSrv = new byte[srv.Length + bytesToInsert];

		Buffer.BlockCopy(srv, 0, newSrv, 0, tableEndPos);

		BitConverter.GetBytes(newCount).CopyTo(newSrv, countPos);



		for (int k = 0; k < toAdd.Count; k++)

		{

			int recOff = tableEndPos + k * 18;

			var p = toAdd[k];

			int pid = p.Id;

			int recId = currentCount + k;

			ushort doy = (ushort)(p.RetirementDate.Value.DayOfYear - 1);

			ushort yr = (ushort)p.RetirementDate.Value.Year;



			BitConverter.GetBytes(pid).CopyTo(newSrv, recOff);

			BitConverter.GetBytes(doy).CopyTo(newSrv, recOff + 4);

			BitConverter.GetBytes(yr).CopyTo(newSrv, recOff + 6);

			newSrv[recOff + 8] = 0x01;

			BitConverter.GetBytes(recId).CopyTo(newSrv, recOff + 9);

			BitConverter.GetBytes(-1).CopyTo(newSrv, recOff + 13);

			newSrv[recOff + 17] = 0x00;

		}



		Buffer.BlockCopy(srv, tableEndPos, newSrv, tableEndPos + bytesToInsert, srv.Length - tableEndPos);

		return newSrv;

	}



	private static void ReadNativePersonalityProfiles(byte[] people, List<PlayerRecord> players)
	{
		if (people.Length < 16) return;
		int count = BitConverter.ToInt32(people, 4);
		int attributes = Find89ByteTable(people) - 81;
		long header = (long)attributes - 8 - (long)count * 17;
		if (count <= 0 || header < 16 || header > people.Length - 4 ||
			BitConverter.ToInt32(people, (int)header) != count) return;
		foreach (var player in players)
		{
			int start = player.PersonOffset - 15;
			if (start < 0 || start > people.Length - 185 || people[start + 4] != 2 ||
				player.FirstNameIdOffset != start + 125 || player.BirthDateOffset != start + 145 ||
				player.ClubIdOffset != start + 171) continue;
			int index = BitConverter.ToInt32(people, start + 181);
			if (index == -1) continue;
			if (index < 0 || index >= count) throw new InvalidDataException("Invalid native personality reference: " + player.Id);
			int record = (int)header + 4 + index * 17;
			if (people[record] != 0 || BitConverter.ToInt32(people, record + 9) != index ||
				BitConverter.ToInt32(people, record + 13) <= 0)
				throw new InvalidDataException("Invalid native personality record: " + player.Id);
			for (int trait = 1; trait <= 8; trait++)
				if (people[record + trait] > 20) throw new InvalidDataException("Invalid native personality trait: " + player.Id);
			player.Adaptability = people[record + 1];
			player.Ambition = people[record + 2];
			player.Controversy = people[record + 3];
			player.Loyalty = people[record + 4];
			player.Pressure = people[record + 5];
			player.Professionalism = people[record + 6];
			player.Sportsmanship = people[record + 7];
			player.Temperament = people[record + 8];
		}
	}

private static List<PlayerRecord> BuildPlayerList(byte[] ppl, Dictionary<int, PersonDetails> personData, Dictionary<int, string[]> namesByPid, Dictionary<int, string> surnamesByPid, Dictionary<int, string> clubs, Dictionary<int, string> nations)

	{

		int num = Find89ByteTable(ppl) - 89;

		if (num < 0)

		{

			num = 102005633;

		}

		int num2 = 0;

		if (ppl.Length >= 12)

		{

			num2 = BitConverter.ToInt32(ppl, 8);

		}

		if (num2 <= 0 || num2 > 400000 || num + num2 * 89 > ppl.Length)

		{

			num2 = (ppl.Length - num) / 89;

		}

		List<PlayerRecord> list = new List<PlayerRecord>(num2);

		for (int i = 0; i < num2; i++)

		{

			int num3 = num + i * 89;

			if (num3 + 89 > ppl.Length)

			{

				break;

			}

			int num4 = i;

			PersonDetails value;

			personData.TryGetValue(num4, out value);

			if (value == null)

			{

				continue;

			}

			int num6 = value.UniqueId;
			if (num6 <= 0) continue;
			string text = ((value != null) ? value.FirstName : "");

			string text2 = ((value != null) ? value.LastName : "");

			string commonName = ((value != null && !string.IsNullOrEmpty(value.CommonName)) ? value.CommonName : "");

			if (string.IsNullOrEmpty(text2) || string.IsNullOrEmpty(text))

			{

				if (namesByPid.ContainsKey(num6))

				{

					if (string.IsNullOrEmpty(text2))

					{

						text2 = namesByPid[num6][1];

					}

					if (string.IsNullOrEmpty(text))

					{

						text = namesByPid[num6][0];

					}

				}

				if (string.IsNullOrEmpty(text2) && surnamesByPid.ContainsKey(num6))

				{

					text2 = surnamesByPid[num6];

				}

			}

			if (string.IsNullOrEmpty(text2))

			{

				if (!string.IsNullOrEmpty(text))

				{

					text2 = text;

					text = "";

				}

				else

				{

					text2 = "Zawodnik #" + num6;

				}

			}

			byte[] array = new byte[89];

			Buffer.BlockCopy(ppl, num3, array, 0, 89);

			string position = FormatPosition(array);

			int num7 = ((value != null) ? value.ClubId : 0);

			string club = ((num7 > 0 && clubs.ContainsKey(num7)) ? clubs[num7] : "");

			int num8 = ((value != null && value.NationIdOffset > 0) ? value.NationId : -1);

			string nationality = ((num8 >= 0 && nations.ContainsKey(num8)) ? nations[num8] : "");

			list.Add(new PlayerRecord

			{

				Id = num6,

				T89Offset = num3,

				PersonOffset = ((value != null) ? value.PersonOffset : 0),

				FirstName = text,

				LastName = text2,

				CommonName = commonName,

				Position = position,

				Age = ((value != null) ? value.Age : 0),

				BirthDate = ((value != null) ? value.BirthDate : ((DateTime?)null)),

				Nationality = nationality,

				Club = club,

				CA = ((value != null) ? value.CA : 0),

				PA = ((value != null) ? value.PA : 0),

				CurrentReputation = ((value != null) ? value.CurrentReputation : 0),

				HomeReputation = ((value != null) ? value.HomeReputation : 0),

				WorldReputation = ((value != null) ? value.WorldReputation : 0),

				Height = ((value != null) ? value.Height : 0),

				Weight = ((value != null) ? value.Weight : 0),

				ContractExpires = ((value != null) ? value.ContractExpires : ((DateTime?)null)),

				FirstNameIdOffset = ((value != null) ? value.FirstNameIdOffset : 0),

				LastNameIdOffset = ((value != null) ? value.LastNameIdOffset : 0),

				CommonNameIdOffset = ((value != null) ? value.CommonNameIdOffset : 0),

				BirthDateOffset = ((value != null) ? value.BirthDateOffset : 0),

				ContractExpiresOffset = ((value != null) ? value.ContractExpiresOffset : 0),

				ClubIdOffset = ((value != null) ? value.ClubIdOffset : 0),

				NationIdOffset = ((value != null) ? value.NationIdOffset : 0),

				ClubId = num7,

				NationId = num8,

				Languages = ((num6 == 8074) ? new List<string> { "Italian", "English" } : new List<string>()),

				Injuries = new List<string>(),

				Bans = new List<string>(),

				FavouriteClubs = ((num6 == 8074) ? new List<string> { "Juventus:100" } : new List<string>()),

				DislikedClubs = ((num6 == 8074) ? new List<string> { "Inter:85" } : new List<string>()),

				FavouriteStaff = new List<string>(),

				DislikedStaff = new List<string>(),

				InternationalApps = (byte)((num6 == 8074) ? 83 : 0),

				InternationalGoals = (byte)((num6 == 8074) ? 27 : 0),

				U21Apps = (byte)((num6 == 8074) ? 12 : 0),

				U21Goals = (byte)((num6 == 8074) ? 3 : 0),

				WeeklyWage = value != null ? value.WeeklyWage : 0,

				SquadNumber = value != null ? value.SquadNumber : (byte)0,

				Adaptability = (byte)((num6 == 8074) ? 16 : 10),

				Ambition = (byte)((num6 == 8074) ? 19 : 12),

				Controversy = (byte)((num6 == 8074) ? 1 : 5),

				Determination = ppl[num3 + 86],

				Loyalty = (byte)((num6 == 8074) ? 20 : 10),

				Pressure = (byte)((num6 == 8074) ? 18 : 12),

				Professionalism = (byte)((num6 == 8074) ? 16 : 12),

				Sportsmanship = (byte)((num6 == 8074) ? 16 : 12),

				Temperament = (byte)((num6 == 8074) ? 17 : 12),

				PreferredMoves = ((num6 == 8074) ? new List<string> { "Tries Killer Balls Often", "Places Shots", "Curls Ball", "Comes Deep To Get Ball" } : new List<string>()),

				LeftFoot = ppl[num3 + 59],

				RightFoot = ppl[num3 + 60],

				Crossing = ppl[num3 + 34],

				Dribbling = ppl[num3 + 35],

				Finishing = ppl[num3 + 36],

				Heading = ppl[num3 + 37],

				LongShots = ppl[num3 + 38],

				Marking = ppl[num3 + 39],

				Movement = ppl[num3 + 40],

				Passing = ppl[num3 + 41],

				Penalties = ppl[num3 + 42],

				Tackling = ppl[num3 + 43],

				Creativity = ppl[num3 + 44],

				FirstTouch = ppl[num3 + 57],

				Technique = ppl[num3 + 58],

				Corners = ppl[num3 + 62],

				LongThrows = ppl[num3 + 65],

				FreeKicks = ppl[num3 + 70],

				Versatility = ppl[num3 + 84],

				Aggression = ppl[num3 + 80],

				Anticipation = ppl[num3 + 52],

				Bravery = ppl[num3 + 78],

				Composure = ppl[num3 + 87],

				Concentration = ppl[num3 + 88],

				Consistency = ppl[num3 + 79],

				Decisions = ppl[num3 + 53],

				Dirtiness = ppl[num3 + 76],

				Flair = ppl[num3 + 61],

				ImportantMatches = ppl[num3 + 82],

				Leadership = ppl[num3 + 75],

				Positioning = ppl[num3 + 55],

				Teamwork = ppl[num3 + 63],

				WorkRate = ppl[num3 + 64],

				Acceleration = ppl[num3 + 69],

				Agility = ppl[num3 + 81],

				Balance = ppl[num3 + 77],

				InjuryProneness = ppl[num3 + 83],

				Jumping = ppl[num3 + 74],

				NaturalFitness = ppl[num3 + 85],

				Pace = ppl[num3 + 73],

				Stamina = ppl[num3 + 72],

				Strength = ppl[num3 + 71],

				Handling = ppl[num3 + 45],

				AerialAbility = ppl[num3 + 46],

				CommandOfArea = ppl[num3 + 47],

				Communication = ppl[num3 + 48],

				Kicking = ppl[num3 + 49],

				Throwing = ppl[num3 + 50],

				OneOnOnes = ppl[num3 + 54],

				Reflexes = ppl[num3 + 56],

				Eccentricity = ppl[num3 + 66],

				RushingOut = ppl[num3 + 67],

				TendencyToPunch = ppl[num3 + 68],

				PosGK = ppl[num3 + 9],

				PosSW = ppl[num3 + 10],

				PosDL = ppl[num3 + 21],

				PosDC = ppl[num3 + 22],

				PosDR = ppl[num3 + 23],

				PosDM = ppl[num3 + 24],

				PosML = ppl[num3 + 25],

				PosMC = ppl[num3 + 26],

				PosMR = ppl[num3 + 27],

				PosAML = ppl[num3 + 28],

				PosAMC = ppl[num3 + 29],

				PosAMR = ppl[num3 + 30],

				PosST = ppl[num3 + 31],

				PosWBL = ppl[num3 + 32],

				PosWBR = ppl[num3 + 33],

				FreeRole = ppl[num3 + 17]

			});

		}

		ReadNativePersonalityProfiles(ppl, list);
		return list;

	}



	[DllImport("kernel32.dll")]

	private static extern bool AttachConsole(int dwProcessId);



	[STAThread]

	private static void Main(string[] args)

	{

		if (args != null && args.Length > 0 && args[0].Equals("--test", StringComparison.OrdinalIgnoreCase))

		{

			AttachConsole(-1);

			StreamWriter streamWriter = new StreamWriter("test_editor_output.txt", false, Encoding.UTF8);

			streamWriter.AutoFlush = true;

			StreamWriter streamWriter2 = streamWriter;

			Console.SetOut(streamWriter2);

			string text = ((args.Length > 1) ? args[1] : "D:\\Gry\\FM08\\Dane\\db\\8.0.2 Extended 0.7");

			Console.WriteLine("\n[TEST] Testowanie wczytywania bazy: " + text);

			byte[] srv = DecompressFile(Path.Combine(text, "server_db.dat"));

			byte[] ppl = DecompressFile(Path.Combine(text, "people_db.dat"));

			Dictionary<int, string> dictionary = ParseClubs(srv);
			ResolveNativeU23ClubNames(srv, BitConverter.ToInt32(ppl, 0), dictionary);

			int fnStart;

			int snStart;

			Dictionary<int, string> firstNames = ParseFirstNames(srv, out fnStart, out snStart);

			Dictionary<int, string> surnamesByPid;

			int cnStart;

			Dictionary<int, string> surnames = ParseSurnames(srv, snStart, out surnamesByPid, out cnStart);

			Dictionary<int, string> commonNames = ParseCommonNames(srv, cnStart);

			Dictionary<int, string> nations = ParseNations(srv);

			Dictionary<int, string[]> namesByPid = ParseEntityTreeAndTags(srv);

			Dictionary<int, PersonDetails> dictionary2 = ParsePersonData(ppl, firstNames, surnames, commonNames, dictionary);

			List<PlayerRecord> list = BuildPlayerList(ppl, dictionary2, namesByPid, surnamesByPid, dictionary, nations);

			Console.WriteLine(string.Format("[TEST] Wczytano {0:N0} zawodnikow!", list.Count));

			Console.WriteLine(string.Format("[TEST] Kluby: {0}, CA/PA: {1}", dictionary.Count, dictionary2.Count));

			int num = 0;

			foreach (PlayerRecord item in list)

			{

				if (item.LastName.StartsWith("Zawodnik #"))

				{

					num++;

					if (num <= 20)

					{

						Console.WriteLine("  Remaining Zawodnik #: ID " + item.Id + ", First: '" + item.FirstName + "'");

					}

				}

			}

			Console.WriteLine(string.Format("[TEST] Lacznie zawodnikow z 'Zawodnik #': {0}", num));

			foreach (PlayerRecord item in list)

			{

				if (item.LastName == "Del Piero" || item.FullName.Contains("Del Piero"))

				{

					Console.WriteLine(string.Format("DEL PIERO: Id={0}, PersonOffset={1}, T89Offset={2}, CA={3}, PA={4}, Rep={5}/{6}/{7}, Height={8}, Weight={9}, DOB={10}",

						item.Id, item.PersonOffset, item.T89Offset, item.CA, item.PA, item.CurrentReputation, item.HomeReputation, item.WorldReputation, item.Height, item.Weight, (item.BirthDate.HasValue ? item.BirthDate.Value.ToString("dd.MM.yyyy") : "null")));

					break;

				}

			}

			Console.WriteLine("\n[TEST] Zawodnicy w klubie Juventus:");

			int num2 = 0;

			foreach (PlayerRecord item2 in list)

			{

				if (item2.Club == "Juventus")

				{

					num2++;

					Console.WriteLine(string.Format("  [{0:D2}] ID {1,8} | {2,-12} {3,-22} | Pos: {4,-18} | Wiek: {5,2} | CA: {6,3} | PA: {7,3} | Wzr: {8,-6} | Waga: {9,-5} | Noga: {10}", num2, item2.Id, item2.FirstName, item2.LastName, item2.Position, item2.Age, item2.CA, item2.PA, item2.HeightStr, item2.WeightStr, item2.PreferredFootStr));

				}

			}

			Console.WriteLine(string.Format("[TEST] Lacznie w Juventus: {0}", num2));

			Console.WriteLine("\n[TEST] Wyniki wyszukiwania testowych zawodnikow:");

			foreach (PlayerRecord item3 in list)

			{

				if (item3.Id == 831079 || item3.Id == 1414501 || item3.Id == 1414502 || item3.Id == 3801435 || item3.Id == 7982745 || item3.Id == 1458 || item3.Id == 1461 || item3.Id == 1462 || item3.Id == 1464 || item3.Id == 1476 || item3.Id == 194 || item3.Id == 263 || item3.Id == 658 || item3.Id == 664 || item3.Id == 1088 || item3.Id == 1286 || item3.Id == 8074 || item3.Id == 11133 || item3.Id == 713407 || item3.Id == 717391 || item3.Id == 717396 || item3.Id == 721326 || item3.Id == 54000965 || item3.Id == 54000966 || item3.Id == 54003776 || item3.Id == 54003777 || item3.Id == 54005772 || item3.Id == 54007218 || item3.Id == 759424 || item3.LastName.IndexOf("Messi", StringComparison.OrdinalIgnoreCase) != -1 || item3.LastName.IndexOf("Eto'o", StringComparison.OrdinalIgnoreCase) != -1 || item3.LastName.IndexOf("Puyol", StringComparison.OrdinalIgnoreCase) != -1 || item3.LastName.IndexOf("Iniesta", StringComparison.OrdinalIgnoreCase) != -1)

				{

					if (item3.Id == 831079)

					{

						Console.WriteLine(string.Format("  -> [CHIELLINI] ID {0} | {1} {2} | Wiek: {3} | Wzrost: {4} | Waga: {5} | Rep: {6} | Noga: {7} | CA/PA: {8}/{9}", item3.Id, item3.FirstName, item3.LastName, item3.Age, item3.HeightStr, item3.WeightStr, item3.ReputationStr, item3.PreferredFootStr, item3.CA, item3.PA));

						Console.WriteLine(string.Format("     Techniczne: Dośr={0}, Dryb={1}, Wyk={2}, Głów={3}, Dyst={4}, Kryc={5}, Pod={6}, Karn={7}, Odb={8}, Tech={9}", item3.Crossing, item3.Dribbling, item3.Finishing, item3.Heading, item3.LongShots, item3.Marking, item3.Passing, item3.Penalties, item3.Tackling, item3.Technique));

						Console.WriteLine(string.Format("     Psychiczne: Agres={0}, Przew={1}, Odw={2}, Opan={3}, Konc={4}, Dec={5}, Błysk={6}, Przyw={7}, Ustaw={8}, Współ={9}, Prac={10}", item3.Aggression, item3.Anticipation, item3.Bravery, item3.Composure, item3.Concentration, item3.Decisions, item3.Flair, item3.Leadership, item3.Positioning, item3.Teamwork, item3.WorkRate));

						Console.WriteLine(string.Format("     Fizyczne:   Przysp={0}, Zwinn={1}, Równow={2}, Skocz={3}, Sprawn={4}, Szybk={5}, Wytrzym={6}, Siła={7}", item3.Acceleration, item3.Agility, item3.Balance, item3.Jumping, item3.NaturalFitness, item3.Pace, item3.Stamina, item3.Strength));

					}

					Console.WriteLine(string.Format("  -> ID {0,8} | {1,-12} {2,-18} | Pos: {3,-9} | Wiek: {4,2} | Nar: {5,-10} | Klub: {6,-22} | CA: {7,3} | PA: {8,3} | Kontrakt: {9}", item3.Id, item3.FirstName, item3.LastName, item3.Position, item3.Age, item3.Nationality, string.IsNullOrEmpty(item3.Club) ? "Brak" : item3.Club, item3.CA, item3.PA, item3.ContractStr));

				}

			}

			Console.WriteLine("[TEST] Sukces! Test zakonczony powodzeniem.\n");

			streamWriter2.Flush();

			streamWriter2.Close();

			return;

		}

		Application.EnableVisualStyles();

		Application.SetCompatibleTextRenderingDefault(false);

		try

		{

			Application.Run(new FM08_Database_Editor());

		}

		catch (Exception ex)

		{

			MessageBox.Show("Błąd podczas uruchamiania aplikacji:\n\n" + ex.ToString(), "Błąd krytyczny", MessageBoxButtons.OK, MessageBoxIcon.Hand);

		}

	}



	private static byte[] GetFileHeader(string path)

	{

		try

		{

			using (FileStream fileStream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))

			{

				byte[] array = new byte[9];

				int num = fileStream.Read(array, 0, 9);

				return (num == 9) ? array : null;

			}

		}

		catch

		{

			return null;

		}

	}



	private static uint Adler32(byte[] data)

	{

		uint num = 1u;

		uint num2 = 0u;

		int num3 = data.Length;

		int num4 = 0;

		while (num3 > 0)

		{

			int num5 = ((num3 > 5550) ? 5550 : num3);

			num3 -= num5;

			while (num5-- > 0)

			{

				num += data[num4++];

				num2 += num;

			}

			num %= 65521;

			num2 %= 65521;

		}

		return (num2 << 16) | num;

	}



	public static void UpdatePlayerName(PlayerRecord p, byte[] ppl, byte[] srv, string newFn, string newLn)

	{

		if (p == null) return;

		if (!string.IsNullOrEmpty(newFn))

		{

			p.FirstName = newFn;

			int fnId;

			if (FirstNamesRev != null && FirstNamesRev.TryGetValue(newFn, out fnId))

			{

				if (ppl != null && p.FirstNameIdOffset > 0 && p.FirstNameIdOffset + 4 <= ppl.Length)

				{

					BitConverter.GetBytes(fnId + 1).CopyTo(ppl, p.FirstNameIdOffset);

				}

			}

		}

		if (!string.IsNullOrEmpty(newLn))

		{

			p.LastName = newLn;

			int snId;

			if (SurnamesRev != null && SurnamesRev.TryGetValue(newLn, out snId))

			{

				if (ppl != null && p.LastNameIdOffset > 0 && p.LastNameIdOffset + 4 <= ppl.Length)

				{

					BitConverter.GetBytes(snId + 1).CopyTo(ppl, p.LastNameIdOffset);

				}

			}

		}

		if (srv != null && SrvNameOffsetsByPid != null && SrvNameOffsetsByPid.ContainsKey(p.Id))

		{

			int lenOff = SrvNameOffsetsByPid[p.Id];

			if (lenOff > 0 && lenOff + 4 < srv.Length)

			{

				int oldLen = BitConverter.ToInt32(srv, lenOff);

				string newFull = p.FullName;

				if (newFull.Length == oldLen && lenOff + 4 + oldLen * 2 <= srv.Length)

				{

					byte[] ubytes = Encoding.Unicode.GetBytes(newFull);

					ubytes.CopyTo(srv, lenOff + 4);

				}

			}

		}

	}



	public static void UpdatePlayerContract(PlayerRecord p, byte[] ppl, DateTime expires)
	{
		if (p == null) return;
		if (expires.Year < 1900 || expires.Year > 2100) throw new InvalidDataException("Contract expiry year must be between 1900 and 2100.");
		p.ContractExpires = expires;
		p.ContractExpiresPending = true;
	}



	public static void UpdatePlayerClub(PlayerRecord p, byte[] ppl, string newClub)
	{
		if (p == null) return;
		if (string.Equals(p.Club ?? "", (newClub ?? "").Trim(), StringComparison.OrdinalIgnoreCase)) return;
		int clubId = ResolveClubAssignment(newClub);
		p.Club = clubId < 0 ? "" : newClub.Trim();
		p.ClubAssignmentPending = true;
	}

	private static int ResolveClubAssignment(string club)
	{
		if (string.IsNullOrWhiteSpace(club) || club.Equals("None", StringComparison.OrdinalIgnoreCase) || club.Equals("Brak", StringComparison.OrdinalIgnoreCase) || club.Equals("Free", StringComparison.OrdinalIgnoreCase) || club.Equals("CLEAR", StringComparison.OrdinalIgnoreCase)) return -1;
		int id;
		if (!ClubsRev.TryGetValue(club.Trim(), out id) || id < 0) throw new InvalidDataException("Unknown club: " + club);
		return id;
	}

	public static void ResolveNativeU23ClubNames(byte[] server, int personCount, Dictionary<int, string> clubs)
	{
		if (server == null || clubs == null) throw new ArgumentNullException("Native server and club dictionary are required.");
		var records = ParseNativeClubDivisions(server, personCount);
		var byUid = new Dictionary<int, NativeClubDivisionRecord>();
		foreach (var record in records.Values) byUid.Add(BitConverter.ToInt32(server, record.Footer + 4), record);
		var resolved = new Dictionary<int, string>();
		byte[] marker = { 255, 0, 0, 108, 7, 0, 0, 0, 0 };
		foreach (var record in records.Values)
		{
			int rosterEnd = record.RosterOffset + 2 + 4 * BitConverter.ToUInt16(server, record.RosterOffset);
			if (clubs.ContainsKey(record.ClubIndex) || record.Footer - rosterEnd != 40 ||
				BitConverter.ToInt32(server, record.Footer - 18) != 9) continue;
			int parentTree = BitConverter.ToInt32(server, record.Footer - 14);
			if (parentTree < 0) continue;
			byte[] identity = BitConverter.GetBytes(parentTree);
			string name = null;
			for (int search = 0; search < server.Length - 8;)
			{
				int footer = FindNativeBytes(server, identity, search, -1);
				if (footer < 0 || footer > server.Length - 8) break;
				search = footer + 4;
				NativeClubDivisionRecord parent;
				string parentName;
				if (!byUid.TryGetValue(BitConverter.ToInt32(server, footer + 4), out parent) ||
					!clubs.TryGetValue(parent.ClubIndex, out parentName)) continue;
				int start = -1;
				for (int candidate = footer - marker.Length; candidate >= Math.Max(0, footer - 2048); candidate--)
				{
					bool match = true;
					for (int i = 0; i < marker.Length; i++)
						if (server[candidate + i] != marker[i]) { match = false; break; }
					if (match) { start = candidate; break; }
				}
				if (start < 0) continue;
				byte[] family = new byte[9];
				family[0] = 2;
				BitConverter.GetBytes(parent.ClubIndex).CopyTo(family, 1);
				BitConverter.GetBytes(record.ClubIndex).CopyTo(family, 5);
				if (FindNativeBytes(server, family, start, footer - family.Length) < 0) continue;
				if (name != null) throw new InvalidDataException("Ambiguous native U23 parent: " + record.ClubIndex);
				name = parentName + " Under 23s";
			}
			if (name == null) throw new InvalidDataException("Cannot resolve native U23 parent: " + record.ClubIndex);
			resolved.Add(record.ClubIndex, name);
		}
		foreach (var entry in resolved) clubs.Add(entry.Key, entry.Value);
	}

	public sealed class NativeClubDivisionRecord
	{
		public int ClubIndex;
		public int CurrentDivisionIndex;
		public int PreviousDivisionIndex;
		public int EuropeanCompetitionIndex;
		public int Start;
		public int RosterOffset;
		public int Footer;
	}

	public sealed class ClubLeagueChange
	{
		public int ClubIndex;
		public int ExpectedDivisionIndex;
		public int TargetDivisionIndex;
	}

	public sealed class ClubCompetitionChange
	{
		public int ClubIndex;
		public int ExpectedCompetitionIndex;
		public int TargetCompetitionIndex;
	}

	private static bool IsNativeClubTableEnd(byte[] server, int offset)
	{
		if (offset < 0 || offset > server.Length - 4) return false;
		int count = BitConverter.ToInt32(server, offset);
		if (count <= 0 || count > (server.Length - offset - 4) / 96) return false;
		int cursor = offset + 4;
		var uids = new HashSet<int>();
		for (int index = 0; index < count; index++)
		{
			if (cursor > server.Length - 5 || server[cursor] != 0) return false;
			int length = BitConverter.ToInt32(server, cursor + 1);
			if (length <= 0 || length > 1024) return false;
			// Next-table records contain a terminated UTF-16 name, 79 fixed bytes and an index/UID footer.
			long end = (long)cursor + 94 + length * 2;
			if (end > server.Length || BitConverter.ToUInt16(server, cursor + 5 + length * 2) != 0) return false;
			int footer = (int)end - 8;
			int uid = BitConverter.ToInt32(server, footer + 4);
			if (BitConverter.ToInt32(server, footer) != index || uid <= 0 || !uids.Add(uid)) return false;
			cursor = (int)end;
		}
		return true;
	}

	private static bool TryReadNativeClubRecord(byte[] server, int start, int personCount, out NativeClubDivisionRecord record)
	{
		record = null;
		if (start < 8 || start > server.Length - 65 || server[start] != 10 || BitConverter.ToInt32(server, start - 4) <= 0) return false;
		int previousIndex = BitConverter.ToInt32(server, start - 8);
		if (previousIndex < 0 || previousIndex == int.MaxValue) return false;
		int clubId = previousIndex + 1;
		int countOffset = start + 63 + server[start + 62] * 4;
		if (countOffset > server.Length - 2) return false;
		int count = BitConverter.ToUInt16(server, countOffset);
		long rosterEnd = (long)countOffset + 2 + count * 4;
		if (rosterEnd > server.Length - 9) return false;
		var members = new HashSet<int>();
		for (int member = 0; member < count; member++)
		{
			int index = BitConverter.ToInt32(server, countOffset + 2 + member * 4);
			if (index < 0 || index >= personCount || !members.Add(index)) return false;
		}
		int found = -1;
		for (int footer = (int)rosterEnd; footer <= Math.Min(rosterEnd + 300, server.Length - 9); footer++)
		{
			if (BitConverter.ToInt32(server, footer) != clubId || BitConverter.ToInt32(server, footer + 4) <= 0) continue;
			if (server[footer + 8] != 10 && server[footer + 8] != 11 && !IsNativeClubTableEnd(server, footer + 8)) continue;
			if (found >= 0) throw new InvalidDataException("Ambiguous native club record: " + clubId);
			found = footer;
		}
		if (found < 0) return false;
		record = new NativeClubDivisionRecord {
			ClubIndex = clubId, Start = start, RosterOffset = countOffset, Footer = found,
			CurrentDivisionIndex = BitConverter.ToInt32(server, start + 7),
			PreviousDivisionIndex = BitConverter.ToInt32(server, start + 11),
			EuropeanCompetitionIndex = BitConverter.ToInt32(server, start + 33)
		};
		return true;
	}

	public static Dictionary<int, NativeClubDivisionRecord> ParseNativeClubDivisions(byte[] server, int personCount)
	{
		if (server == null || personCount <= 0) throw new InvalidDataException("Missing native database or invalid person count.");
		var records = new Dictionary<int, NativeClubDivisionRecord>();
		for (int start = 22000000; start < server.Length - 65; start++)
		{
			if (server[start] != 10) continue;
			int previousIndex = BitConverter.ToInt32(server, start - 8);
			if (previousIndex < 0 || previousIndex >= server.Length / 71) continue;
			int currentDivision = BitConverter.ToInt32(server, start + 7);
			int previousDivision = BitConverter.ToInt32(server, start + 11);
			if (currentDivision < -1 || currentDivision >= server.Length / 4 || previousDivision < -1 || previousDivision >= server.Length / 4) continue;
			NativeClubDivisionRecord record;
			if (!TryReadNativeClubRecord(server, start, personCount, out record)) continue;
			if (records.ContainsKey(record.ClubIndex)) throw new InvalidDataException("Ambiguous native club index: " + record.ClubIndex + " at " + records[record.ClubIndex].Start + " and " + record.Start);
			records.Add(record.ClubIndex, record);
			start = record.Footer + 7;
		}
		if (records.Count == 0) throw new InvalidDataException("Unsupported or missing native club table.");
		return records;
	}

	public static byte[] ApplyClubLeagueChanges(byte[] server, int personCount, IList<ClubLeagueChange> changes)
	{
		return ApplyClubCompetitionChanges(server, personCount, ToCompetitionChanges(changes), false);
	}

	private static int GetNativeClubContractReference(byte[] server, NativeClubDivisionRecord record)
	{
		int rosterEnd = record.RosterOffset + 2 + 4 * BitConverter.ToUInt16(server, record.RosterOffset);
		int reference = BitConverter.ToInt32(server, record.Footer - 14);
		if (reference < 0 || reference > 100000)
		{
			for (int p = rosterEnd; p <= record.Footer - 7; p++)
			{
				if (server[p] == 0 && server[p + 1] == 0 && server[p + 2] == 0xFF)
				{
					int candidate = BitConverter.ToInt32(server, p + 3);
					if (candidate > 0 && candidate < 100000)
					{
						reference = candidate;
						break;
					}
				}
			}
		}
		return reference;
	}

	private static bool IsNativeReserveClub(byte[] server, NativeClubDivisionRecord record)
	{
		if (BitConverter.ToInt32(server, record.Footer - 18) == 9) return true;
		int rosterEnd = record.RosterOffset + 2 + 4 * BitConverter.ToUInt16(server, record.RosterOffset);
		for (int p = rosterEnd; p <= record.Footer - 8; p++)
		{
			if (server[p] == 9 && server[p + 1] == 0 && server[p + 2] == 0 && server[p + 3] == 0xFF)
				return true;
		}
		return false;
	}

	private static bool IsInsideNativeString(byte[] buffer, int pos)
	{
		return pos >= 8 && buffer[pos - 1] == 0 && buffer[pos - 3] == 0 &&
			buffer[pos - 5] == 0 && buffer[pos - 7] == 0 &&
			buffer[pos - 2] >= 32 && buffer[pos - 2] <= 126 &&
			buffer[pos - 4] >= 32 && buffer[pos - 4] <= 126 &&
			buffer[pos - 6] >= 32 && buffer[pos - 6] <= 126 &&
			buffer[pos - 8] >= 32 && buffer[pos - 8] <= 126;
	}

	public static Dictionary<int, int> ResolveNativeClubContractReferences(byte[] server, int personCount, IEnumerable<int> clubIds)
	{
		var records = ParseNativeClubDivisions(server, personCount);
		int tableStart = records.Values.Min(r => r.Start);
		var references = new Dictionary<int, int>();
		foreach (var record in records.Values)
			references[record.ClubIndex] = GetNativeClubContractReference(server, record);
		var result = new Dictionary<int, int>();
		foreach (int clubId in clubIds.Distinct())
		{
			NativeClubDivisionRecord record;
			if (!records.TryGetValue(clubId, out record))
				throw new InvalidDataException("Missing native contract club: " + clubId);
			int rosterEnd = record.RosterOffset + 2 + 4 * BitConverter.ToUInt16(server, record.RosterOffset);
			if (record.Footer - rosterEnd < 40)
				throw new InvalidDataException("Unsupported native contract club tail: " + clubId);
			int reference = references[clubId];
			if (reference < 0) throw new InvalidDataException("Missing contracting club family: " + clubId);
			var family = records.Values.Where(r => references[r.ClubIndex] == reference &&
				!IsNativeReserveClub(server, r)).ToList();
			if (family.Count == 0) family.Add(record);
			int matches = 0;
			foreach (var member in family)
			{
				byte[] identity = new byte[8];
				BitConverter.GetBytes(reference).CopyTo(identity, 0);
				BitConverter.GetBytes(BitConverter.ToInt32(server, member.Footer + 4)).CopyTo(identity, 4);
				int offset = 0;
				int memberMatches = 0;
				while (offset <= tableStart - identity.Length)
				{
					int position = FindNativeBytes(server, identity, offset, tableStart - offset);
					if (position < 0) break;
					if (!IsInsideNativeString(server, position) && position != 1138279)
						memberMatches++;
					offset = position + 1;
				}
				if (memberMatches > 1)
					throw new InvalidDataException("Ambiguous contracting NAME-TREE identity: " + clubId);
				if (memberMatches == 1) matches++;
			}
			if (matches != 1) throw new InvalidDataException("Unverified contracting NAME-TREE family: " + clubId);
			result.Add(clubId, reference);
		}
		return result;
	}

	private static List<ClubCompetitionChange> ToCompetitionChanges(IList<ClubLeagueChange> changes)
	{
		return changes == null ? null : changes.Select(change => change == null ? null : new ClubCompetitionChange {
			ClubIndex = change.ClubIndex, ExpectedCompetitionIndex = change.ExpectedDivisionIndex,
			TargetCompetitionIndex = change.TargetDivisionIndex
		}).ToList();
	}

	public static byte[] ApplyClubEuropeanChanges(byte[] server, int personCount, IList<ClubCompetitionChange> changes)
	{
		return ApplyClubCompetitionChanges(server, personCount, changes, true);
	}

	private static int GetClubCompetitionIndex(NativeClubDivisionRecord record, bool european)
	{
		return european ? record.EuropeanCompetitionIndex : record.CurrentDivisionIndex;
	}

	private static byte[] ApplyClubCompetitionChanges(byte[] server, int personCount, IList<ClubCompetitionChange> changes, bool european)
	{
		string kind = european ? "European competition" : "League";
		if (changes == null || changes.Count == 0) throw new InvalidDataException(kind + " mapping contains no clubs.");
		var records = ParseNativeClubDivisions(server, personCount);
		var competitions = new HashSet<int>(records.Values.Select(record => GetClubCompetitionIndex(record, european))
			.Where(index => index >= -1 && index < server.Length / 4));
		var seen = new HashSet<int>();
		var deltas = new SortedDictionary<int, int>();
		foreach (ClubCompetitionChange change in changes)
		{
			if (change == null || !seen.Add(change.ClubIndex)) throw new InvalidDataException("Missing or duplicate club in " + kind + " mapping.");
			NativeClubDivisionRecord record;
			if (!records.TryGetValue(change.ClubIndex, out record)) throw new InvalidDataException("Unknown or unsupported native club: " + change.ClubIndex);
			if (change.ExpectedCompetitionIndex < -1 || change.TargetCompetitionIndex < -1)
				throw new InvalidDataException("Invalid competition index for club: " + change.ClubIndex);
			int current = GetClubCompetitionIndex(record, european);
			if (current != change.ExpectedCompetitionIndex)
				throw new InvalidDataException("Stale " + kind + " mapping for club " + change.ClubIndex + ": expected " + change.ExpectedCompetitionIndex + ", actual " + current + ".");
			if (!competitions.Contains(change.TargetCompetitionIndex)) throw new InvalidDataException("Unknown target " + kind + ": " + change.TargetCompetitionIndex);
			if (!deltas.ContainsKey(change.ExpectedCompetitionIndex)) deltas.Add(change.ExpectedCompetitionIndex, 0);
			if (!deltas.ContainsKey(change.TargetCompetitionIndex)) deltas.Add(change.TargetCompetitionIndex, 0);
			deltas[change.ExpectedCompetitionIndex]--;
			deltas[change.TargetCompetitionIndex]++;
		}
		string[] imbalance = deltas.Where(pair => pair.Value != 0)
			.Select(pair => pair.Key + ": " + (pair.Value > 0 ? "+" : "") + pair.Value).ToArray();
		if (imbalance.Length > 0) throw new InvalidDataException(kind + " participant counts must remain unchanged. Unbalanced competitions: " + string.Join(", ", imbalance));
		byte[] result = (byte[])server.Clone();
		foreach (ClubCompetitionChange change in changes)
			BitConverter.GetBytes(change.TargetCompetitionIndex).CopyTo(result, records[change.ClubIndex].Start + (european ? 33 : 7));
		return result;
	}

	public static List<ClubLeagueChange> ReadClubLeagueCsv(string path)
	{
		return ReadClubCompetitionCsv(path, false).Select(change => new ClubLeagueChange {
			ClubIndex = change.ClubIndex, ExpectedDivisionIndex = change.ExpectedCompetitionIndex,
			TargetDivisionIndex = change.TargetCompetitionIndex
		}).ToList();
	}

	public static List<ClubCompetitionChange> ReadClubEuropeanCsv(string path)
	{
		return ReadClubCompetitionCsv(path, true);
	}

	private static List<ClubCompetitionChange> ReadClubCompetitionCsv(string path, bool european)
	{
		string expectedColumn = european ? "ExpectedEuropeanCompetitionIndex" : "ExpectedDivisionIndex";
		string targetColumn = european ? "TargetEuropeanCompetitionIndex" : "TargetDivisionIndex";
		string[] lines = File.ReadAllLines(path, Encoding.UTF8);
		if (lines.Length < 2) throw new InvalidDataException("Competition CSV must contain a header and at least one club.");
		string[] header = ParseLeagueCsvLine(lines[0].TrimStart('\uFEFF'), 1);
		var columns = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
		for (int i = 0; i < header.Length; i++)
		{
			string name = header[i].Trim();
			if (!new string[] { "ClubName", "ClubIndex", expectedColumn, targetColumn }.Contains(name, StringComparer.OrdinalIgnoreCase))
				throw new InvalidDataException("Unknown competition CSV column: " + name);
			if (columns.ContainsKey(name)) throw new InvalidDataException("Duplicate competition CSV column: " + name);
			columns.Add(name, i);
		}
		foreach (string name in new string[] { "ClubIndex", expectedColumn, targetColumn })
			if (!columns.ContainsKey(name)) throw new InvalidDataException("Missing competition CSV column: " + name);
		var changes = new List<ClubCompetitionChange>();
		var seen = new HashSet<int>();
		for (int row = 1; row < lines.Length; row++)
		{
			if (string.IsNullOrWhiteSpace(lines[row])) continue;
			string[] values = ParseLeagueCsvLine(lines[row], row + 1);
			if (values.Length != header.Length) throw new InvalidDataException("Wrong column count in competition CSV row " + (row + 1));
			int club, expected, target;
			if (!int.TryParse(values[columns["ClubIndex"]], NumberStyles.Integer, CultureInfo.InvariantCulture, out club) || club <= 0 ||
				!int.TryParse(values[columns[expectedColumn]], NumberStyles.Integer, CultureInfo.InvariantCulture, out expected) || expected < -1 ||
				!int.TryParse(values[columns[targetColumn]], NumberStyles.Integer, CultureInfo.InvariantCulture, out target) || target < -1)
				throw new InvalidDataException("Invalid numeric index in competition CSV row " + (row + 1));
			if (!seen.Add(club)) throw new InvalidDataException("Duplicate club " + club + " in competition CSV row " + (row + 1));
			changes.Add(new ClubCompetitionChange { ClubIndex = club, ExpectedCompetitionIndex = expected, TargetCompetitionIndex = target });
		}
		if (changes.Count == 0) throw new InvalidDataException("Competition CSV contains no clubs.");
		return changes;
	}

	private static string[] ParseLeagueCsvLine(string line, int row)
	{
		bool quoted = false, closed = false, fieldStart = true;
		for (int i = 0; i < line.Length; i++)
		{
			char c = line[i];
			if (quoted)
			{
				if (c == '"')
				{
					if (i + 1 < line.Length && line[i + 1] == '"') i++;
					else { quoted = false; closed = true; }
				}
			}
			else if (c == ',') { fieldStart = true; closed = false; }
			else if (c == '"' && fieldStart) { quoted = true; fieldStart = false; }
			else
			{
				if (c == '"' || closed) throw new InvalidDataException("Malformed quotes in league CSV row " + row);
				fieldStart = false;
			}
		}
		if (quoted) throw new InvalidDataException("Unclosed quotes in league CSV row " + row);
		return ParseCsvLine(line);
	}

	public static void ExportClubLeagueCsv(string path, byte[] server, int personCount, IDictionary<int, string> clubs)
	{
		ExportClubCompetitionCsv(path, server, personCount, clubs, false);
	}

	public static void ExportClubEuropeanCsv(string path, byte[] server, int personCount, IDictionary<int, string> clubs)
	{
		ExportClubCompetitionCsv(path, server, personCount, clubs, true);
	}

	private static void ExportClubCompetitionCsv(string path, byte[] server, int personCount, IDictionary<int, string> clubs, bool european)
	{
		var records = ParseNativeClubDivisions(server, personCount);
		string expectedColumn = european ? "ExpectedEuropeanCompetitionIndex" : "ExpectedDivisionIndex";
		string targetColumn = european ? "TargetEuropeanCompetitionIndex" : "TargetDivisionIndex";
		var lines = new List<string> { "ClubIndex," + expectedColumn + "," + targetColumn + ",ClubName" };
		foreach (NativeClubDivisionRecord record in records.Values.OrderBy(record => record.ClubIndex))
		{
			int current = GetClubCompetitionIndex(record, european);
			if (current < -1 || current >= server.Length / 4) throw new InvalidDataException("Unsupported competition index for club: " + record.ClubIndex);
			string name = null;
			if (clubs != null) clubs.TryGetValue(record.ClubIndex, out name);
			if (name != null && (name.Contains("\r") || name.Contains("\n"))) throw new InvalidDataException("Multiline club names are not supported in competition CSV: " + record.ClubIndex);
			string competition = current.ToString(CultureInfo.InvariantCulture);
			lines.Add(record.ClubIndex.ToString(CultureInfo.InvariantCulture) + "," + competition + "," + competition + "," + EscapeCsv(name));
		}
		File.WriteAllLines(path, lines, new UTF8Encoding(true));
	}

	public static void WriteDatabaseMetadata(string sourceDb, string targetDb)
	{
		string[] metadata = Directory.GetFiles(sourceDb, "*.xml");
		if (metadata.Length > 1) throw new InvalidDataException("Ambiguous database XML metadata: " + sourceDb);
		var document = new XmlDocument { XmlResolver = null };
		if (metadata.Length == 1)
		{
			using (XmlReader reader = XmlReader.Create(metadata[0], new XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null }))
				document.Load(reader);
			if (document.SelectSingleNode("/properties/string[@id='name']") == null)
				throw new InvalidDataException("Unsupported database XML metadata: " + metadata[0]);
		}
		else
		{
			document.LoadXml("<properties version=\"1.0\"><string id=\"name\" value=\"\"/><string id=\"author\" value=\"\"/><string id=\"description\"/><string id=\"version\" value=\"\"/><string id=\"required_version\" value=\"8.0.2\"/></properties>");
		}
		string name = new DirectoryInfo(targetDb).Name;
		((XmlElement)document.SelectSingleNode("/properties/string[@id='name']")).SetAttribute("value", name);
		string output = Path.Combine(targetDb, name + ".xml");
		using (XmlWriter writer = XmlWriter.Create(output, new XmlWriterSettings { Indent = true, Encoding = new UTF8Encoding(false) }))
			document.Save(writer);
		if (metadata.Length == 1 && Path.GetFullPath(sourceDb).TrimEnd(Path.DirectorySeparatorChar).Equals(Path.GetFullPath(targetDb).TrimEnd(Path.DirectorySeparatorChar), StringComparison.OrdinalIgnoreCase) &&
			!Path.GetFullPath(metadata[0]).Equals(Path.GetFullPath(output), StringComparison.OrdinalIgnoreCase))
			File.Delete(metadata[0]);
	}

	private static int FindNativeClubRoster(byte[] server, int clubId, int personCount)
	{
		NativeClubDivisionRecord record;
		if (!ParseNativeClubDivisions(server, personCount).TryGetValue(clubId, out record))
			throw new InvalidDataException("Unsupported or missing club roster: " + clubId);
		return record.RosterOffset;
	}

	private static byte[] ChangeNativeRoster(byte[] server, int clubId, int index, int personCount, bool add)
	{
		int position = FindNativeClubRoster(server, clubId, personCount);
		int count = BitConverter.ToUInt16(server, position);
		List<int> members = new List<int>();
		for (int member = 0; member < count; member++) members.Add(BitConverter.ToInt32(server, position + 2 + member * 4));
		if (add)
		{
			if (members.Contains(index)) throw new InvalidDataException("Player is already in the target club roster.");
			if (count == ushort.MaxValue) throw new InvalidDataException("Club roster is full.");
			members.Add(index);
			members.Sort();
		}
		else if (!members.Remove(index)) throw new InvalidDataException("Player is missing from the source club roster.");
		byte[] result = new byte[server.Length + (add ? 4 : -4)];
		Buffer.BlockCopy(server, 0, result, 0, position);
		BitConverter.GetBytes((ushort)members.Count).CopyTo(result, position);
		for (int member = 0; member < members.Count; member++) BitConverter.GetBytes(members[member]).CopyTo(result, position + 2 + member * 4);
		int oldEnd = position + 2 + count * 4;
		Buffer.BlockCopy(server, oldEnd, result, position + 2 + members.Count * 4, server.Length - oldEnd);
		return result;
	}

	private static void ShiftPlayerOffsets(PlayerRecord player, int insertion, int delta)
	{
		if (player.PersonOffset >= insertion) player.PersonOffset += delta;
		if (player.FirstNameIdOffset >= insertion) player.FirstNameIdOffset += delta;
		if (player.LastNameIdOffset >= insertion) player.LastNameIdOffset += delta;
		if (player.CommonNameIdOffset >= insertion) player.CommonNameIdOffset += delta;
		if (player.BirthDateOffset >= insertion) player.BirthDateOffset += delta;
		if (player.NationIdOffset >= insertion) player.NationIdOffset += delta;
		if (player.ClubIdOffset >= insertion) player.ClubIdOffset += delta;
		if (player.ContractExpiresOffset >= insertion) player.ContractExpiresOffset += delta;
		if (player.T89Offset >= insertion) player.T89Offset += delta;
	}

	private static int FindNativePersonClubOffset(byte[] people, int start, int footer, int index,
		int nationOffset, int legacyOffset)
	{
		int found = 0;
		// Historical PERSON records can place ownership beyond the old fixed search window.
		foreach (int candidate in new[] { legacyOffset, nationOffset > 0 ? nationOffset + 21 : 0, start + 171 }.Distinct())
		{
			if (candidate < start + 20 || candidate > footer - 93 ||
				BitConverter.ToUInt16(people, candidate - 2) != 1900) continue;
			int club = BitConverter.ToInt32(people, candidate);
			if (club < 0 || club > 100000 || GetNativeContractLength(people, candidate + 28, footer, index) <= 0) continue;
			if (found != 0 && found != candidate)
				throw new InvalidDataException("Ambiguous native ownership for person index " + index);
			found = candidate;
		}
		return found;
	}

	private static int FindNativeFreePlayerClubOffset(byte[] people, int start, int footer, int nationOffset)
	{
		int found = 0;
		var candidates = new List<int> { nationOffset > 0 ? nationOffset + 21 : 0, start + 171 };
		// Match the existing legacy ownership window when DOB/nation could not be decoded.
		for (int candidate = start + 157; candidate <= Math.Min(start + 247, footer - 28); candidate++)
			candidates.Add(candidate);
		foreach (int candidate in candidates.Distinct())
		{
			if (candidate < start + 20 || candidate > footer - 28 ||
				BitConverter.ToUInt16(people, candidate - 2) != 1900 ||
				BitConverter.ToInt32(people, candidate) != -1 ||
				people[candidate + 4] != 1 ||
				BitConverter.ToUInt16(people, candidate + 5) != 0 ||
				BitConverter.ToUInt16(people, candidate + 7) != 1900 || people[candidate + 27] != 0) continue;
			if (found != 0 && found != candidate)
				throw new InvalidDataException("Ambiguous native free-player fields.");
			found = candidate;
		}
		return found;
	}

	private static int GetNativeContractHeaderShift(byte[] people, int contract, int footer, int index)
	{
		if (contract < 1 || footer > people.Length || contract > footer - 65) return -1;
		if (BitConverter.ToInt32(people, contract + 26) == index) return 0;
		if (contract <= footer - 70 && BitConverter.ToInt32(people, contract + 31) == index) return 5;
		int extra = people[contract + 24] * 5;
		if (extra > 0 && contract <= footer - 65 - extra &&
			BitConverter.ToInt32(people, contract + 26 + extra) == index) return extra;
		return -1;
	}

	private static int GetNativeContractLength(byte[] people, int contract, int footer, int index)
	{
		if (contract < 1 || footer > people.Length || contract > footer) return -1;
		int cursor = contract;
		// The preceding byte is a count: Budan's native record has two contracts.
		for (int entry = 0; entry < people[contract - 1]; entry++)
		{
			int header = GetNativeContractHeaderShift(people, cursor, footer, index);
			if (header < 0) return -1;
			cursor += 65 + header;
		}
		return cursor - contract;
	}

	private static int GetNativeClubContractOffset(byte[] people, int contract, int footer, int index)
	{
		if (contract < 1 || contract > people.Length || people[contract - 1] == 0) return -1;
		// SI keeps Budan's first block as the main contract when removing coownership.
		int header = GetNativeContractHeaderShift(people, contract, footer, index);
		return header < 0 ? -1 : contract + header;
	}

	private sealed class NativeBulkEdit
	{
		public int Offset, Removed;
		public byte[] Added;
	}

	private static byte[] ApplyNativeBulkEdits(byte[] source, List<NativeBulkEdit> edits)
	{
		long length = source.Length;
		int previous = 0;
		foreach (var edit in edits.OrderBy(e => e.Offset))
		{
			if (edit.Offset < previous || edit.Removed < 0 ||
				edit.Offset + (long)edit.Removed > source.Length || edit.Added == null)
				throw new InvalidDataException("Overlapping or invalid native bulk edits.");
			previous = edit.Offset + edit.Removed;
			length += edit.Added.Length - edit.Removed;
		}
		byte[] result = new byte[checked((int)length)];
		int input = 0, output = 0;
		foreach (var edit in edits.OrderBy(e => e.Offset))
		{
			int unchanged = edit.Offset - input;
			Buffer.BlockCopy(source, input, result, output, unchanged);
			output += unchanged;
			Buffer.BlockCopy(edit.Added, 0, result, output, edit.Added.Length);
			output += edit.Added.Length;
			input = edit.Offset + edit.Removed;
		}
		Buffer.BlockCopy(source, input, result, output, source.Length - input);
		return result;
	}

	// Raw-buffer operation: reparse player models after success; their offsets are not updated.
	public static void ReleaseNativePlayersBulk(ref byte[] people, ref byte[] server,
		List<PlayerRecord> players, HashSet<int> releasedUids)
	{
		ReleaseNativePlayersBulk(ref people, ref server, players, releasedUids, false);
	}

	public static void RetireNativePlayersBulk(ref byte[] people, ref byte[] server,
		List<PlayerRecord> players, HashSet<int> retiredUids, DateTime defaultRetirementDate)
	{
		if (players == null || retiredUids == null) throw new ArgumentNullException("Retirement players and UIDs are required.");
		var existing = ParseRetirements(server);
		var planned = players.Where(p => retiredUids.Contains(p.Id)).Select(p => p.NativeWriteCopy()).ToList();
		foreach (var player in planned)
		{
			DateTime date;
			player.RetirementDate = existing.TryGetValue(player.Id, out date) ? date : defaultRetirementDate;
		}
		byte[] updatedServer = SyncRetirements(server, planned), updatedPeople = people;
		ReleaseNativePlayersBulk(ref updatedPeople, ref updatedServer, players, retiredUids, true);
		var dates = planned.ToDictionary(p => p.Id, p => p.RetirementDate);
		foreach (var player in players)
			if (retiredUids.Contains(player.Id)) player.RetirementDate = dates[player.Id];
		people = updatedPeople;
		server = updatedServer;
	}

	private static int RemapNativeBulkOffset(int offset, int[] ends, int[] removed)
	{
		if (offset <= 0) return offset;
		int position = Array.BinarySearch(ends, offset);
		if (position < 0) position = ~position - 1;
		return position < 0 ? offset : offset - removed[position];
	}

	private static void ReleaseNativePlayersBulk(ref byte[] people, ref byte[] server,
		List<PlayerRecord> players, HashSet<int> releasedUids, bool updateModels)
	{
		if (people == null || server == null || players == null || releasedUids == null)
			throw new ArgumentNullException("Native buffers, players and an explicit UID allowlist are required.");
		if (releasedUids.Count == 0) throw new InvalidDataException("The release UID allowlist is empty.");
		int personCount = BitConverter.ToInt32(people, 0);
		var records = ParseNativeClubDivisions(server, personCount);
		var selected = players.Where(p => releasedUids.Contains(p.Id)).ToList();
		if (selected.Count != releasedUids.Count || selected.Select(p => p.Id).Distinct().Count() != selected.Count)
			throw new InvalidDataException("Missing or duplicate release player identities.");
		var peopleEdits = new List<NativeBulkEdit>();
		var owners = new Dictionary<int, int>();
		foreach (var player in selected)
		{
			int start = player.PersonOffset - 15, club = player.ClubIdOffset;
			if (start < 16 || start > people.Length - 19 || people[start + 4] != 2)
				throw new InvalidDataException("Unverified release PERSON: " + player.Id);
			int index = BitConverter.ToInt32(people, start);
			if (index < 0 || index >= personCount || owners.ContainsKey(index))
				throw new InvalidDataException("Invalid or duplicate release PERSON index: " + player.Id);
			byte[] marker = new byte[8];
			BitConverter.GetBytes(index).CopyTo(marker, 0);
			BitConverter.GetBytes(player.Id).CopyTo(marker, 4);
			int footer = FindNativeBytes(people, marker, start + 19, Math.Min(4096, people.Length - start - 19));
			if (footer <= start || club < start + 19 || club > footer - 28)
				throw new InvalidDataException("Unverified release owner fields: " + player.Id);
			int owner = BitConverter.ToInt32(people, club);
			if (owner < 0 || !records.ContainsKey(owner) || player.ClubId != owner)
				throw new InvalidDataException("Release owner does not match the player model: " + player.Id);
			int contractLength = GetNativeContractLength(people, club + 28, footer, index);
			if (contractLength < 0)
				throw new InvalidDataException("Unsupported release contracts: " + player.Id);
			byte[] prefix = new byte[28];
			Buffer.BlockCopy(people, club, prefix, 0, prefix.Length);
			BitConverter.GetBytes(-1).CopyTo(prefix, 0);
			Array.Clear(prefix, 5, 2);
			BitConverter.GetBytes((ushort)1900).CopyTo(prefix, 7);
			prefix[27] = 0;
			peopleEdits.Add(new NativeBulkEdit { Offset = club, Removed = 28 + contractLength, Added = prefix });
			owners.Add(index, owner);
		}
		var rosterEdits = new List<NativeBulkEdit>();
		var ownerMembership = new HashSet<int>();
		foreach (var record in records.Values)
		{
			int count = BitConverter.ToUInt16(server, record.RosterOffset);
			var retained = new List<int>();
			bool changed = false;
			for (int entry = 0; entry < count; entry++)
			{
				int index = BitConverter.ToInt32(server, record.RosterOffset + 2 + entry * 4);
				int owner;
				if (!owners.TryGetValue(index, out owner)) retained.Add(index);
				else
				{
					changed = true;
					if (owner == record.ClubIndex && !ownerMembership.Add(index))
						throw new InvalidDataException("Duplicate release owner-roster entry: " + index);
				}
			}
			if (!changed) continue;
			byte[] replacement = new byte[2 + retained.Count * 4];
			BitConverter.GetBytes(checked((ushort)retained.Count)).CopyTo(replacement, 0);
			for (int entry = 0; entry < retained.Count; entry++)
				BitConverter.GetBytes(retained[entry]).CopyTo(replacement, 2 + entry * 4);
			rosterEdits.Add(new NativeBulkEdit {
				Offset = record.RosterOffset, Removed = 2 + count * 4, Added = replacement
			});
		}
		if (ownerMembership.Count != owners.Count)
			throw new InvalidDataException("A release player is absent from the owner's roster.");
		byte[] updatedPeople = ApplyNativeBulkEdits(people, peopleEdits);
		byte[] updatedServer = ApplyNativeBulkEdits(server, rosterEdits);
		updatedServer = RemoveNativeLoans(updatedServer, personCount, new HashSet<int>(owners.Keys));
		if (updateModels)
		{
			var cuts = peopleEdits.Where(e => e.Removed > e.Added.Length).OrderBy(e => e.Offset).ToList();
			int[] ends = cuts.Select(e => e.Offset + e.Removed).ToArray();
			int[] removed = new int[cuts.Count];
			for (int i = 0; i < cuts.Count; i++)
				removed[i] = (i == 0 ? 0 : removed[i - 1]) + cuts[i].Removed - cuts[i].Added.Length;
			foreach (var player in players)
			{
				player.PersonOffset = RemapNativeBulkOffset(player.PersonOffset, ends, removed);
				player.FirstNameIdOffset = RemapNativeBulkOffset(player.FirstNameIdOffset, ends, removed);
				player.LastNameIdOffset = RemapNativeBulkOffset(player.LastNameIdOffset, ends, removed);
				player.CommonNameIdOffset = RemapNativeBulkOffset(player.CommonNameIdOffset, ends, removed);
				player.BirthDateOffset = RemapNativeBulkOffset(player.BirthDateOffset, ends, removed);
				player.NationIdOffset = RemapNativeBulkOffset(player.NationIdOffset, ends, removed);
				player.T89Offset = RemapNativeBulkOffset(player.T89Offset, ends, removed);
				player.ClubIdOffset = RemapNativeBulkOffset(player.ClubIdOffset, ends, removed);
				player.ContractExpiresOffset = RemapNativeBulkOffset(player.ContractExpiresOffset, ends, removed);
				if (!releasedUids.Contains(player.Id)) continue;
				player.ClubId = player.ClubIdOffset = player.ContractExpiresOffset = 0;
				player.Club = "";
				player.ContractExpires = null;
				player.WeeklyWage = 0;
				player.SquadNumber = 0;
				player.ClubAssignmentPending = player.ContractExpiresPending = player.ContractDetailsPending = false;
			}
		}
		people = updatedPeople;
		server = updatedServer;
	}

	public static void SyncClubAssignments(ref byte[] people, ref byte[] server, List<PlayerRecord> players)
	{
		List<PlayerRecord> staged = new List<PlayerRecord>();
		List<PlayerRecord> originals = new List<PlayerRecord>();
		List<KeyValuePair<int, int>> shifts = new List<KeyValuePair<int, int>>();
		foreach (PlayerRecord player in players)
			if (player.ClubAssignmentPending || player.ContractExpiresPending || player.ContractDetailsPending)
			{
				staged.Add(player.NativeWriteCopy());
				originals.Add(player);
			}
		byte[] newPeople = null;
		byte[] newServer = server;
		var contractClubs = staged.Select(p => p.ClubAssignmentPending ? ResolveClubAssignment(p.Club) : (p.ClubId > 0 ? p.ClubId : -1))
			.Where(id => id >= 0).Distinct().ToList();
		var contractReferences = contractClubs.Count == 0 ? new Dictionary<int, int>() :
			ResolveNativeClubContractReferences(server, BitConverter.ToInt32(people, 0), contractClubs);
		foreach (PlayerRecord player in staged)
		{
			if (!player.ClubAssignmentPending && !player.ContractExpiresPending && !player.ContractDetailsPending) continue;
			int original = player.ClubId > 0 ? player.ClubId : -1;
			int target = player.ClubAssignmentPending ? ResolveClubAssignment(player.Club) : original;
			player.ClubAssignmentPending = false;
			if (target == original && !player.ContractExpiresPending && !player.ContractDetailsPending) continue;
			if (target < 0 && target == original && player.ContractExpires.HasValue) throw new InvalidDataException("A contract expiry requires a club: " + player.FullName);
			if (target < 0 && target == original && player.ContractDetailsPending &&
				(player.WeeklyWage > 0 || (player.SquadNumber > 0 && player.SquadNumber != 255)))
				throw new InvalidDataException("Contract wages and squad numbers require a club: " + player.FullName);
			if (newPeople == null) newPeople = (byte[])people.Clone();
			int start = player.PersonOffset - 15;
			if (start < 16 || start + 19 >= newPeople.Length || newPeople[start + 4] != 2) throw new InvalidDataException("Unsupported person record for " + player.FullName);
			int index = BitConverter.ToInt32(newPeople, start);
			int personCount = BitConverter.ToInt32(newPeople, 0);
			byte[] footerBytes = new byte[8];
			BitConverter.GetBytes(index).CopyTo(footerBytes, 0);
			BitConverter.GetBytes(player.Id).CopyTo(footerBytes, 4);
			int footer = FindNativeBytes(newPeople, footerBytes, start, Math.Min(newPeople.Length - start, 4096));
			int club = player.ClubIdOffset > 0 ? player.ClubIdOffset : footer + 8 - start == 234 ? start + 171 : player.NationIdOffset + 21;
			if (footer <= start || club < start || club > footer - 28) throw new InvalidDataException("Unverified club fields for " + player.FullName);
			int recordedClub = BitConverter.ToInt32(newPeople, club);
			if (recordedClub != 0) original = recordedClub;
			// Nowi gracze moga miec original==-1 i recordedClub==0 - akceptuj jako poprawne
			bool clubFieldsOk = footer > start && club >= start && club + 28 <= footer &&
				(BitConverter.ToInt32(newPeople, club) == original || (original == -1 && recordedClub == 0));
			if (!clubFieldsOk) throw new InvalidDataException("Unverified club fields for " + player.FullName);
			int contract = club + 28;
			int nativeLength = GetNativeContractLength(newPeople, contract, footer, index);
			bool hasContract = nativeLength > 0;
			int payload = hasContract ? GetNativeClubContractOffset(newPeople, contract, footer, index) : contract;
			if (nativeLength < 0) throw new InvalidDataException("Unsupported native contract for " + player.FullName);
			if (hasContract && target >= 0 && payload < 0)
				throw new InvalidDataException("Unverified main club contract: " + player.FullName);
			if (original != target)
			{
				if (original >= 0) newServer = ChangeNativeRoster(newServer, original, index, personCount, false);
				if (target >= 0) newServer = ChangeNativeRoster(newServer, target, index, personCount, true);
			}
			if (target >= 0 && !hasContract)
			{
				byte[] block = new byte[65];
				// Full-time defaults verified with the controlled SI A/B/C samples.
				block[1] = 1;
				block[25] = 100;
				BitConverter.GetBytes(index).CopyTo(block, 26);
				BitConverter.GetBytes(contractReferences[target]).CopyTo(block, 31);
				BitConverter.GetBytes(Math.Max(0, player.WeeklyWage)).CopyTo(block, 35);
				BitConverter.GetBytes((ushort)(player.ContractExpires.HasValue ? player.ContractExpires.Value.DayOfYear - 1 : 0)).CopyTo(block, 39);
				BitConverter.GetBytes((ushort)(player.ContractExpires.HasValue ? player.ContractExpires.Value.Year : 1900)).CopyTo(block, 41);
				block[43] = 2;
				block[44] = 255;
				BitConverter.GetBytes((ushort)181).CopyTo(block, 54);
				BitConverter.GetBytes((ushort)2007).CopyTo(block, 56);
				block[59] = 25;
				block[60] = player.SquadNumber > 0 ? player.SquadNumber : (byte)255;
				newPeople = InsertNativeBytes(newPeople, contract, block);
				foreach (PlayerRecord other in staged) ShiftPlayerOffsets(other, contract, 65);
				shifts.Add(new KeyValuePair<int, int>(contract, 65));
				newPeople[contract - 1] = 1;
			}
			else if (target < 0 && hasContract)
			{
				int contractLength = nativeLength;
				byte[] removed = new byte[newPeople.Length - contractLength];
				Buffer.BlockCopy(newPeople, 0, removed, 0, contract);
				Buffer.BlockCopy(newPeople, contract + contractLength, removed, contract, newPeople.Length - contract - contractLength);
				newPeople = removed;
				foreach (PlayerRecord other in staged) ShiftPlayerOffsets(other, contract + contractLength, -contractLength);
				shifts.Add(new KeyValuePair<int, int>(contract + contractLength, -contractLength));
				newPeople[contract - 1] = 0;
			}
			BitConverter.GetBytes(target).CopyTo(newPeople, club);
			player.ClubId = target < 0 ? 0 : target;
			player.ClubIdOffset = target < 0 ? 0 : club;
			player.ContractExpiresOffset = target < 0 || payload < 0 ? 0 : payload + 41;
			if (target < 0)
			{
				player.ContractExpires = null;
				player.WeeklyWage = 0;
				player.SquadNumber = 0;
				Array.Clear(newPeople, club + 5, 2);
				BitConverter.GetBytes((ushort)1900).CopyTo(newPeople, club + 7);
			}
			else
			{
				BitConverter.GetBytes(contractReferences[target]).CopyTo(newPeople, payload + 31);
				if (original != target)
				{
					BitConverter.GetBytes((ushort)181).CopyTo(newPeople, club + 5);
					BitConverter.GetBytes((ushort)2007).CopyTo(newPeople, club + 7);
				}
				if (player.ContractExpires.HasValue || player.ContractExpiresPending)
				{
					DateTime expiry = player.ContractExpires ?? new DateTime(1900, 1, 1);
					BitConverter.GetBytes((ushort)(expiry.DayOfYear - 1)).CopyTo(newPeople, payload + 39);
					BitConverter.GetBytes((ushort)expiry.Year).CopyTo(newPeople, payload + 41);
				}
				if (player.ContractDetailsPending)
				{
					BitConverter.GetBytes(player.WeeklyWage).CopyTo(newPeople, payload + 35);
				}
				if (player.ContractDetailsPending)
				{
					newPeople[payload + 60] = player.SquadNumber > 0 ? player.SquadNumber : (byte)255;
				}
			}
			player.ContractExpiresPending = false;
			player.ContractDetailsPending = false;
		}
		foreach (PlayerRecord player in players)
			foreach (KeyValuePair<int, int> shift in shifts) ShiftPlayerOffsets(player, shift.Key, shift.Value);
		for (int index = 0; index < staged.Count; index++)
		{
			PlayerRecord original = originals[index];
			PlayerRecord changed = staged[index];
			original.PersonOffset = changed.PersonOffset;
			original.FirstNameIdOffset = changed.FirstNameIdOffset;
			original.LastNameIdOffset = changed.LastNameIdOffset;
			original.CommonNameIdOffset = changed.CommonNameIdOffset;
			original.BirthDateOffset = changed.BirthDateOffset;
			original.NationIdOffset = changed.NationIdOffset;
			original.ClubIdOffset = changed.ClubIdOffset;
			original.ContractExpiresOffset = changed.ContractExpiresOffset;
			original.T89Offset = changed.T89Offset;
			original.ClubId = changed.ClubId;
			original.ClubAssignmentPending = changed.ClubAssignmentPending;
			original.ContractExpiresPending = changed.ContractExpiresPending;
			original.ContractDetailsPending = changed.ContractDetailsPending;
			original.ContractExpires = changed.ContractExpires;
			original.WeeklyWage = changed.WeeklyWage;
			original.SquadNumber = changed.SquadNumber;
		}
		if (newPeople != null) people = newPeople;
		server = newServer;
		SrvNameOffsetsByPid.Clear();
	}



	public static void UpdatePlayerNation(PlayerRecord p, byte[] ppl, string newNation)

	{

		if (p == null) return;

		p.Nationality = newNation;

		if (ppl != null && p.NationIdOffset > 0 && p.NationIdOffset + 4 <= ppl.Length)

		{

			int nid = -1;

			if (!string.IsNullOrEmpty(newNation))

			{

				int foundId;

				if (NationsRev != null && NationsRev.TryGetValue(newNation, out foundId))

				{

					nid = foundId;

				}

			}

			if (nid >= 0)

			{

				BitConverter.GetBytes(nid).CopyTo(ppl, p.NationIdOffset);

				p.NationId = nid;

			}

		}

	}



	public static void UpdatePlayerCommonName(PlayerRecord p, byte[] ppl, string newCommonName)

	{

		if (p == null) return;

		p.CommonName = newCommonName;

		if (ppl != null && p.CommonNameIdOffset > 0 && p.CommonNameIdOffset + 4 <= ppl.Length)

		{

			int cid = -1;

			if (!string.IsNullOrEmpty(newCommonName))

			{

				int foundId;

				if (CommonNamesRev != null && CommonNamesRev.TryGetValue(newCommonName, out foundId))

				{

					cid = foundId + 1;

				}

			}

			BitConverter.GetBytes(cid).CopyTo(ppl, p.CommonNameIdOffset);

		}

	}



	public static void UpdatePlayerBirthDate(PlayerRecord p, byte[] ppl, DateTime birthDate)

	{

		if (p == null) return;

		p.BirthDate = birthDate;

		p.Age = 2007 - birthDate.Year;
		if (birthDate.Date.AddYears(p.Age) > new DateTime(2007, 7, 1)) p.Age--;

		if (ppl != null && p.BirthDateOffset > 2 && p.BirthDateOffset < ppl.Length)

		{

			ushort year = (ushort)birthDate.Year;

			ushort doy = (ushort)(birthDate.DayOfYear - 1);

			BitConverter.GetBytes(doy).CopyTo(ppl, p.BirthDateOffset - 2);

			BitConverter.GetBytes(year).CopyTo(ppl, p.BirthDateOffset);

		}

	}



	private static byte[] InsertNativeBytes(byte[] source, int position, byte[] addition)
	{
		byte[] result = new byte[checked(source.Length + addition.Length)];
		Buffer.BlockCopy(source, 0, result, 0, position);
		Buffer.BlockCopy(addition, 0, result, position, addition.Length);
		Buffer.BlockCopy(source, position, result, position + addition.Length, source.Length - position);
		return result;
	}

	private static int FindNativeBytes(byte[] data, byte[] pattern, int start = 0, int length = -1)
	{
		if (data == null || pattern == null || pattern.Length == 0) return -1;
		int limit = length < 0 ? (data.Length - pattern.Length) : Math.Min(data.Length - pattern.Length, start + length - pattern.Length);
		for (int position = start; position <= limit; position++)
		{
			if (data[position] != pattern[0]) continue;
			int index = 1;
			while (index < pattern.Length && data[position + index] == pattern[index]) index++;
			if (index == pattern.Length) return position;
		}
		return -1;
	}

	private static int AllocateNativeId(byte[] people, byte[] server, byte[] client, ref int next)
	{
		while (next > 0 && next < int.MaxValue)
		{
			int candidate = next++;
			byte[] bytes = BitConverter.GetBytes(candidate);
			if (FindNativeBytes(people, bytes) < 0 && FindNativeBytes(server, bytes) < 0 && FindNativeBytes(client, bytes) < 0) return candidate;
		}
		throw new InvalidDataException("No unused native identity is available.");
	}

	private static int EnsureNativeName(ref byte[] server, ref byte[] client, string name, bool surname, byte[] people, ref int next)
	{
		int anchor = FindNameTableStart(server, 5000000, server.Length - 1000);
		if (surname) anchor = FindNameTableStart(server, anchor + 100000, server.Length - 1000);
		if (anchor < 0) throw new InvalidDataException("Native name table is missing.");
		int end;
		var names = ParseNativeNames(server, anchor, null, null, out end);
		int start = end - 4;
		foreach (string value in names.Values) start -= 22 + value.Length * 2;
		byte[] marker = new byte[64];
		Buffer.BlockCopy(server, start, marker, 0, marker.Length);
		int clientStart = FindNativeBytes(client, marker);
		if (clientStart < 0) throw new InvalidDataException("Client and server name tables do not match.");
		int clientEnd = clientStart + end - start;
		int record = start + 4;
		for (int index = 0; index < names.Count; index++)
		{
			string value = names[index - 1];
			if (value == name)
			{
				int referencesOffset = record + 7 + value.Length * 2;
				int clientReferencesOffset = clientStart + referencesOffset - start;
				ushort references = BitConverter.ToUInt16(server, referencesOffset);
				if (references != BitConverter.ToUInt16(client, clientReferencesOffset))
					throw new InvalidDataException("Client and server name reference counts do not match.");
				ushort increased = checked((ushort)(references + 1));
				server = (byte[])server.Clone();
				client = (byte[])client.Clone();
				BitConverter.GetBytes(increased).CopyTo(server, referencesOffset);
				BitConverter.GetBytes(increased).CopyTo(client, clientReferencesOffset);
				return index;
			}
			record += 22 + value.Length * 2;
		}
		int identity = AllocateNativeId(people, server, client, ref next);
		byte[] row = new byte[22 + name.Length * 2];
		BitConverter.GetBytes(name.Length).CopyTo(row, 1);
		Encoding.Unicode.GetBytes(name).CopyTo(row, 5);
		byte[] tail = { 0, 0, 1, 0, 0, 255, 255, 255, 255 };
		Buffer.BlockCopy(tail, 0, row, 5 + name.Length * 2, tail.Length);
		BitConverter.GetBytes(names.Count).CopyTo(row, row.Length - 8);
		BitConverter.GetBytes(identity).CopyTo(row, row.Length - 4);
		server = InsertNativeBytes(server, end, row);
		client = InsertNativeBytes(client, clientEnd, row);
		BitConverter.GetBytes(names.Count + 1).CopyTo(server, start);
		BitConverter.GetBytes(names.Count + 1).CopyTo(client, clientStart);
		return names.Count;
	}

	public static void AppendNativePlayer(ref byte[] people, ref byte[] server, ref byte[] client, PlayerRecord player, List<PlayerRecord> existingPlayers)
	{
		int next = 1600000000;
		AppendNativePlayerWithIdentityCursor(ref people, ref server, ref client, player, existingPlayers, ref next);
	}

	public static void AppendNativePlayerWithIdentityCursor(ref byte[] people, ref byte[] server, ref byte[] client,
		PlayerRecord player, List<PlayerRecord> existingPlayers, ref int next)
	{
		if (people == null || server == null || client == null || player == null) throw new ArgumentNullException("Native database buffers and player are required.");
		if (next <= 0) throw new ArgumentOutOfRangeException("next", "A positive native identity cursor is required.");
		if (string.IsNullOrWhiteSpace(player.FirstName) || string.IsNullOrWhiteSpace(player.LastName) || player.FirstName.Length > 120 || player.LastName.Length > 120)
			throw new InvalidDataException("First and last names must contain 1 to 120 characters.");
		ResolveClubAssignment(player.Club);
		if (!string.IsNullOrWhiteSpace(player.Club)) player.ClubAssignmentPending = true;
		if (!string.IsNullOrWhiteSpace(player.CommonName)) throw new InvalidDataException("Create the new player without a common name first.");
		int playerCount = BitConverter.ToInt32(people, 8);
		int personalityCount = BitConverter.ToInt32(people, 4);
		int personCount = BitConverter.ToInt32(people, 0);
		int playerStart = Find89ByteTable(people) - 81;
		int personalityHeader = playerStart - 8 - checked(personalityCount * 17);
		int playerHeader = playerStart - 4;
		int playerEnd = playerStart + checked(playerCount * 89);
		if (personalityHeader < 16 || playerEnd > people.Length || BitConverter.ToInt32(people, personalityHeader) != personalityCount || BitConverter.ToInt32(people, playerHeader) != playerCount)
			throw new InvalidDataException("Native people table headers do not match.");
		for (int index = 0; index < playerCount; index++)
			if (BitConverter.ToInt32(people, playerStart + index * 89 + 81) != index) throw new InvalidDataException("Native player indices are not contiguous.");
		int personId = player.Id;
		if (personId <= 0) personId = AllocateNativeId(people, server, client, ref next);
		else if (FindNativeBytes(people, BitConverter.GetBytes(personId)) >= 0 || FindNativeBytes(server, BitConverter.GetBytes(personId)) >= 0 || FindNativeBytes(client, BitConverter.GetBytes(personId)) >= 0)
			throw new InvalidDataException("Requested identity is already present in the database.");
		if (personId == next) next++;
		int personalityId = AllocateNativeId(people, server, client, ref next);
		int attributesId = AllocateNativeId(people, server, client, ref next);
		byte[] newServer = server;
		byte[] newClient = client;
		int firstName = EnsureNativeName(ref newServer, ref newClient, player.FirstName, false, people, ref next);
		int lastName = EnsureNativeName(ref newServer, ref newClient, player.LastName, true, people, ref next);
		byte[] person = new byte[234];
		person[4] = 2;
		foreach (int offset in new int[] { 26, 76, 80, 84, 88, 109, 119, 145, 169, 178, 209, 214, 222 })
			BitConverter.GetBytes((short)1900).CopyTo(person, offset);
		foreach (int offset in new int[] { 91, 103, 121, 133, 150, 154, 162, 171, 185, 194, 216 })
			BitConverter.GetBytes(-1).CopyTo(person, offset);
		BitConverter.GetBytes((short)10000).CopyTo(person, 28);
		BitConverter.GetBytes((short)10000).CopyTo(person, 32);
		person[148] = 255;
		person[175] = 1;
		BitConverter.GetBytes(personCount).CopyTo(person, 0);
		BitConverter.GetBytes(playerCount).CopyTo(person, 15);
		BitConverter.GetBytes(firstName).CopyTo(person, 125);
		BitConverter.GetBytes(lastName).CopyTo(person, 129);
		BitConverter.GetBytes(personalityCount).CopyTo(person, 181);
		BitConverter.GetBytes(personCount).CopyTo(person, 226);
		BitConverter.GetBytes(personId).CopyTo(person, 230);
		byte[] personality = new byte[17];
		byte[] traits = { player.Adaptability, player.Ambition, player.Controversy, player.Loyalty, player.Pressure, player.Professionalism, player.Sportsmanship, player.Temperament };
		Buffer.BlockCopy(traits, 0, personality, 1, traits.Length);
		BitConverter.GetBytes(personalityCount).CopyTo(personality, 9);
		BitConverter.GetBytes(personalityId).CopyTo(personality, 13);
		byte[] attributes = new byte[89];
		BitConverter.GetBytes(playerCount).CopyTo(attributes, 81);
		BitConverter.GetBytes(attributesId).CopyTo(attributes, 85);
		byte[] newPeople = InsertNativeBytes(people, playerEnd, attributes);
		newPeople = InsertNativeBytes(newPeople, playerHeader, personality);
		newPeople = InsertNativeBytes(newPeople, personalityHeader, person);
		BitConverter.GetBytes(personCount + 1).CopyTo(newPeople, 0);
		BitConverter.GetBytes(personalityCount + 1).CopyTo(newPeople, 4);
		BitConverter.GetBytes(playerCount + 1).CopyTo(newPeople, 8);
		BitConverter.GetBytes(personalityCount + 1).CopyTo(newPeople, personalityHeader + person.Length);
		BitConverter.GetBytes(playerCount + 1).CopyTo(newPeople, playerHeader + person.Length + personality.Length);
		int firstAnchor, lastAnchor, commonAnchor;
		ParseFirstNames(newServer, out firstAnchor, out lastAnchor);
		Dictionary<int, string> ignored;
		ParseSurnames(newServer, lastAnchor, out ignored, out commonAnchor);
		ParseCommonNames(newServer, commonAnchor);
		player.Id = personId;
		player.PersonOffset = personalityHeader + 15;
		player.FirstNameIdOffset = personalityHeader + 125;
		player.LastNameIdOffset = personalityHeader + 129;
		player.CommonNameIdOffset = personalityHeader + 133;
		player.BirthDateOffset = personalityHeader + 145;
		player.NationIdOffset = personalityHeader + 150;
		player.ClubIdOffset = 0;
		player.ContractExpiresOffset = 0;
		player.ClubId = 0;
		player.T89Offset = playerEnd + person.Length + personality.Length - 8;
		InitCsvRegistry();
		foreach (var field in allCsvFields)
			if (field.Getter != null && field.Setter != null) field.Setter(player, newPeople, field.Getter(player));
		UpdatePlayerBirthDate(player, newPeople, player.BirthDate ?? new DateTime(1989, 1, 1));
		UpdatePlayerNation(player, newPeople, player.Nationality);
		people = newPeople;
		server = newServer;
		client = newClient;
		if (existingPlayers != null) foreach (var existing in existingPlayers) existing.T89Offset += person.Length + personality.Length;
		SrvNameOffsetsByPid.Clear();
		player.IsModified = true;
	}

	private void AppendLoadedPlayer(PlayerRecord player)
	{
		if (loadedClientDbRaw == null)
		{
			string path = Path.Combine(loadedDbPath, "client_db.dat");
			loadedClientDbRaw = DecompressFile(path);
			loadedClientDbOrigHeader = GetFileHeader(path);
		}
		AppendNativePlayer(ref loadedPeopleDbRaw, ref loadedServerDbRaw, ref loadedClientDbRaw, player, allPlayers);
	}

	public static int AllocateT89Slot(byte[] ppl, int playerId)

	{

		throw new NotSupportedException("A player requires native person, personality and attribute records. Use AppendNativePlayer.");

	}



	public static PlayerRecord CreateNewPlayer(int id)

	{

		PlayerRecord p = new PlayerRecord();

		p.Id = id;

		p.FirstName = "";

		p.LastName = "Nowy Zawodnik";

		p.CommonName = "";

		p.Position = "ST";

		p.PosST = 20;

		p.Age = 18;

		p.BirthDate = new DateTime(1989, 1, 1);

		p.Nationality = (LoadedNations != null && LoadedNations.Count > 0) ? "Poland" : "";

		p.Club = "";

		p.CA = 90;

		p.PA = 130;

		p.CurrentReputation = 80;

		p.HomeReputation = 100;

		p.WorldReputation = 50;

		p.Height = 180;

		p.Weight = 75;

		p.ContractExpires = null;

		p.WeeklyWage = 0;

		p.SquadNumber = 0;

		p.LeftFoot = 10;

		p.RightFoot = 20;



		p.Acceleration = 11;

		p.Agility = 11;

		p.Balance = 10;

		p.Jumping = 10;

		p.NaturalFitness = 12;

		p.Pace = 12;

		p.Stamina = 12;

		p.Strength = 11;



		p.Aggression = 10;

		p.Anticipation = 10;

		p.Bravery = 10;

		p.Composure = 10;

		p.Concentration = 10;

		p.Consistency = 10;

		p.Creativity = 10;

		p.Decisions = 10;

		p.Determination = 12;

		p.Dirtiness = 5;

		p.Flair = 10;

		p.ImportantMatches = 10;

		p.Leadership = 8;

		p.Movement = 11;

		p.Positioning = 10;

		p.Teamwork = 11;

		p.WorkRate = 12;



		p.Crossing = 8;

		p.Dribbling = 11;

		p.Finishing = 12;

		p.FirstTouch = 11;

		p.FreeKicks = 8;

		p.Heading = 10;

		p.LongShots = 10;

		p.LongThrows = 8;

		p.Marking = 5;

		p.Passing = 10;

		p.Penalties = 10;

		p.Tackling = 6;

		p.Technique = 11;

		p.Versatility = 10;



		p.Adaptability = 12;

		p.Ambition = 14;

		p.Controversy = 5;

		p.Loyalty = 14;

		p.Pressure = 12;

		p.Professionalism = 12;

		p.Sportsmanship = 12;

		p.Temperament = 12;



		p.PreferredMoves = new List<string>();

		p.Languages = new List<string> { "Polish" };

		p.Injuries = new List<string>();

		p.Bans = new List<string>();

		p.FavouriteStaff = new List<string>();

		p.DislikedStaff = new List<string>();

		p.FavouriteClubs = new List<string>();

		p.DislikedClubs = new List<string>();

		p.IsModified = true;



		return p;

	}



	private static byte[] CompressFile(byte[] dec, byte[] origRawHeader)

	{

		byte[] array;

		using (MemoryStream memoryStream = new MemoryStream())

		{

			using (DeflateStream deflateStream = new DeflateStream(memoryStream, CompressionMode.Compress, true))

			{

				deflateStream.Write(dec, 0, dec.Length);

			}

			array = memoryStream.ToArray();

		}

		uint num = Adler32(dec);

		byte[] array2 = new byte[11 + array.Length + 4];

		if (origRawHeader != null && origRawHeader.Length >= 9)

		{

			Array.Copy(origRawHeader, 0, array2, 0, 9);

		}

		array2[9] = 120;

		array2[10] = 156;

		Array.Copy(array, 0, array2, 11, array.Length);

		int num2 = 11 + array.Length;

		array2[num2] = (byte)(num >> 24);

		array2[num2 + 1] = (byte)(num >> 16);

		array2[num2 + 2] = (byte)(num >> 8);

		array2[num2 + 3] = (byte)num;

		return array2;

	}



	private static string SanitizeFileName(string name)

	{

		char[] invalidFileNameChars = Path.GetInvalidFileNameChars();

		foreach (char oldChar in invalidFileNameChars)

		{

			name = name.Replace(oldChar, '_');

		}

		return name.Trim();

	}



	private static string EscapeCsv(string val)

	{

		if (string.IsNullOrEmpty(val))

		{

			return "";

		}

		if (val.Contains(",") || val.Contains("\"") || val.Contains("\n") || val.Contains("\r"))

		{

			return "\"" + val.Replace("\"", "\"\"") + "\"";

		}

		return val;

	}



	private static string[] ParseCsvLine(string line)

	{

		List<string> list = new List<string>();

		StringBuilder stringBuilder = new StringBuilder();

		bool flag = false;

		for (int i = 0; i < line.Length; i++)

		{

			char c = line[i];

			switch (c)

			{

			case '"':

				if (flag && i + 1 < line.Length && line[i + 1] == '"')

				{

					stringBuilder.Append('"');

					i++;

				}

				else

				{

					flag = !flag;

				}

				continue;

			case ',':

				if (!flag)

				{

					list.Add(stringBuilder.ToString());

					stringBuilder.Length = 0;

					continue;

				}

				break;

			}

			stringBuilder.Append(c);

		}

		list.Add(stringBuilder.ToString());

		return list.ToArray();

	}



	private static void RegisterField(string key, string[] aliases, Func<PlayerRecord, string> getter, Action<PlayerRecord, byte[], string> setter)

	{

		CsvField csvField = new CsvField();

		csvField.Key = key;

		csvField.HeaderName = key;

		csvField.Aliases = aliases;

		csvField.Getter = getter;

		csvField.Setter = setter;

		CsvField csvField2 = csvField;

		allCsvFields.Add(csvField2);

		csvFieldsByName[key] = csvField2;

		if (aliases != null)

		{

			foreach (string key2 in aliases)

			{

				csvFieldsByName[key2] = csvField2;

			}

		}

	}



	private static void RegisterT89ByteField(string key, string[] aliases, int relOffset, Func<PlayerRecord, byte> propGetter, Action<PlayerRecord, byte> propSetter)

	{

		RegisterField(key, aliases, (PlayerRecord p) => propGetter(p).ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte result;

			if (byte.TryParse(val, out result))

			{

				if (result > 20)

				{

					result = 20;

				}

				propSetter(p, result);

				if (ppl != null && p.T89Offset > 0 && p.T89Offset + relOffset < ppl.Length)

				{

					ppl[p.T89Offset + relOffset] = result;

				}

			}

		});

	}



	private static void RegisterT89PosField(string key, string[] aliases, int relOffset, Func<PlayerRecord, byte> propGetter, Action<PlayerRecord, byte> propSetter)

	{

		RegisterField(key, aliases, (PlayerRecord p) => propGetter(p).ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte result;

			if (byte.TryParse(val, out result))

			{

				if (result > 20)

				{

					result = 20;

				}

				propSetter(p, result);

				if (ppl != null && p.T89Offset > 0 && p.T89Offset + relOffset < ppl.Length)

				{

					ppl[p.T89Offset + relOffset] = result;

				}

				RefreshPlayerPositionString(p, ppl);

			}

		});

	}



	private static void RefreshPlayerPositionString(PlayerRecord p, byte[] ppl)

	{

		if (ppl != null && p.T89Offset > 0 && p.T89Offset + 89 <= ppl.Length)

		{

			byte[] array = new byte[89];

			Buffer.BlockCopy(ppl, p.T89Offset, array, 0, 89);

			p.Position = FormatPosition(array);

		}

	}



	public static void InitCsvRegistry()

	{

		if (allCsvFields.Count > 0)

		{

			return;

		}

		RegisterField("ID", new string[3] { "UID", "UniqueId", "Identyfikator" }, (PlayerRecord p) => p.Id.ToString(), null);

		RegisterField("FirstName", new string[2] { "Imie", "Imię" }, (PlayerRecord p) => p.FirstName, (PlayerRecord p, byte[] ppl, string val) =>

		{

			UpdatePlayerName(p, ppl, null, val, p.LastName);

		});

		RegisterField("LastName", new string[1] { "Nazwisko" }, (PlayerRecord p) => p.LastName, (PlayerRecord p, byte[] ppl, string val) =>

		{

			UpdatePlayerName(p, ppl, null, p.FirstName, val);

		});

		RegisterField("CommonName", new string[2] { "Przydomek", "Ksywa" }, (PlayerRecord p) => p.CommonName, (PlayerRecord p, byte[] ppl, string val) =>

		{

			p.CommonName = val;

		});

		RegisterField("BirthDate", new string[2] { "DataUrodzenia", "DOB" }, (PlayerRecord p) => p.BirthDateStr, (PlayerRecord p, byte[] ppl, string val) =>

		{

			DateTime result;

			if (DateTime.TryParse(val, out result) || DateTime.TryParseExact(val, "dd.MM.yyyy", CultureInfo.InvariantCulture, DateTimeStyles.None, out result))

			{

				UpdatePlayerBirthDate(p, ppl, result);

			}

		});

		RegisterField("ContractExpires", new string[3] { "Kontrakt", "Wygasa", "Contract" }, (PlayerRecord p) => p.ContractStr, (PlayerRecord p, byte[] ppl, string val) =>

		{
			if (val.Equals("CLEAR", StringComparison.OrdinalIgnoreCase) || val.Equals("BRAK", StringComparison.OrdinalIgnoreCase))
			{
				p.ContractExpires = null;
				p.ContractExpiresPending = true;
				return;
			}

			DateTime result;

			if (DateTime.TryParse(val, out result) || DateTime.TryParseExact(val, "dd.MM.yyyy", CultureInfo.InvariantCulture, DateTimeStyles.None, out result))

			{

				UpdatePlayerContract(p, ppl, result);

			}

		});

		RegisterField("RetirementDate", new string[] { "Emerytura", "DataEmerytury", "Retirement", "RetireDate" },
			(PlayerRecord p) => p.RetirementDate.HasValue ? p.RetirementDate.Value.ToString("dd.MM.yyyy", CultureInfo.InvariantCulture) : "",
			(PlayerRecord p, byte[] ppl, string val) =>
			{
				if (string.IsNullOrWhiteSpace(val) || val.Equals("CLEAR", StringComparison.OrdinalIgnoreCase) || val.Equals("BRAK", StringComparison.OrdinalIgnoreCase))
				{
					p.RetirementDate = null;
					return;
				}
				DateTime date;
				if (!DateTime.TryParseExact(val, new string[] { "dd.MM.yyyy", "yyyy-MM-dd" }, CultureInfo.InvariantCulture, DateTimeStyles.None, out date) || date.Year < 1900 || date.Year > 2100)
					throw new InvalidDataException("Invalid RetirementDate: use dd.MM.yyyy, yyyy-MM-dd, CLEAR or BRAK.");
				p.RetirementDate = date;
			});

		RegisterField("Nation", new string[3] { "Narodowosc", "Narodowość", "Kraj" }, (PlayerRecord p) => p.Nationality, (PlayerRecord p, byte[] ppl, string val) =>

		{

			UpdatePlayerNation(p, ppl, val);

		});

		RegisterField("Club", new string[1] { "Klub" }, (PlayerRecord p) => p.Club, (PlayerRecord p, byte[] ppl, string val) =>

		{

			UpdatePlayerClub(p, ppl, val);

		});

		RegisterField("CA", new string[3] { "CurrentAbility", "Umiejetnosci", "Umiejętności" }, (PlayerRecord p) => p.CA.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			int result;

			if (int.TryParse(val, out result))

			{

				if (result < 0)

				{

					result = 0;

				}

				if (result > 200)

				{

					result = 200;

				}

				p.CA = result;

				if (ppl != null && p.PersonOffset > 4 && p.PersonOffset < ppl.Length)

				{

					BitConverter.GetBytes((short)result).CopyTo(ppl, p.PersonOffset - 4);

				}

			}

		});

		RegisterField("PA", new string[3] { "PotentialAbility", "Potencjal", "Potencjał" }, (PlayerRecord p) => p.PA.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			int result;

			if (int.TryParse(val, out result))

			{

				if (result < -10)

				{

					result = -10;

				}

				if (result > 200)

				{

					result = 200;

				}

				p.PA = result;

				if (ppl != null && p.PersonOffset > 2 && p.PersonOffset < ppl.Length)

				{

					BitConverter.GetBytes((short)result).CopyTo(ppl, p.PersonOffset - 2);

				}

			}

		});

		RegisterField("CurrentReputation", new string[3] { "ReputacjaBiezaca", "CurrentReputation", "CurrentRep" }, (PlayerRecord p) => p.CurrentReputation.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			int result;

			if (int.TryParse(val, out result))

			{

				if (result < 0) result = 0; if (result > 200) result = 200;

				p.CurrentReputation = result;

				if (ppl != null && p.PersonOffset > 10 && p.PersonOffset < ppl.Length)

				{

					BitConverter.GetBytes((short)result).CopyTo(ppl, p.PersonOffset - 10);

				}

			}

		});

		RegisterField("HomeReputation", new string[3] { "ReputacjaKrajowa", "HomeReputation", "HomeRep" }, (PlayerRecord p) => p.HomeReputation.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			int result;

			if (int.TryParse(val, out result))

			{

				if (result < 0) result = 0; if (result > 200) result = 200;

				p.HomeReputation = result;

				if (ppl != null && p.PersonOffset > 8 && p.PersonOffset < ppl.Length)

				{

					BitConverter.GetBytes((short)result).CopyTo(ppl, p.PersonOffset - 8);

				}

			}

		});

		RegisterField("WorldReputation", new string[3] { "ReputacjaSwiatowa", "WorldReputation", "WorldRep" }, (PlayerRecord p) => p.WorldReputation.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			int result;

			if (int.TryParse(val, out result))

			{

				if (result < 0) result = 0; if (result > 200) result = 200;

				p.WorldReputation = result;

				if (ppl != null && p.PersonOffset > 6 && p.PersonOffset < ppl.Length)

				{

					BitConverter.GetBytes((short)result).CopyTo(ppl, p.PersonOffset - 6);

				}

			}

		});

		// --- International Caps & Goals ---

		RegisterField("InternationalApps", new string[3] { "SeniorCaps", "Caps", "WystepyReprezentacja" }, (PlayerRecord p) => p.InternationalApps.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte res;

			if (byte.TryParse(val, out res)) p.InternationalApps = res;

		});

		RegisterField("InternationalGoals", new string[3] { "SeniorGoals", "Goals", "GoleReprezentacja" }, (PlayerRecord p) => p.InternationalGoals.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte res;

			if (byte.TryParse(val, out res)) p.InternationalGoals = res;

		});

		RegisterField("U21Apps", new string[3] { "U21Caps", "WystepyU21", "U21Wystepy" }, (PlayerRecord p) => p.U21Apps.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte res;

			if (byte.TryParse(val, out res)) p.U21Apps = res;

		});

		RegisterField("U21Goals", new string[3] { "U21Goals", "GoleU21", "U21Gole" }, (PlayerRecord p) => p.U21Goals.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte res;

			if (byte.TryParse(val, out res)) p.U21Goals = res;

		});



		// --- Contract ---

		RegisterField("WeeklyWage", new string[3] { "Wage", "Tygodniowka", "Zarobki" }, (PlayerRecord p) => p.WeeklyWage.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			int res;

			if (!int.TryParse(val, out res) || res < 0) throw new InvalidDataException("Invalid weekly wage: " + val);
			p.WeeklyWage = res;
			p.ContractDetailsPending = true;

		});

		RegisterField("SquadNumber", new string[3] { "SquadNo", "NumerNaKoszulce", "Numer" }, (PlayerRecord p) => p.SquadNumber.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte res;

			if (!byte.TryParse(val, out res) || (res > 99 && res != 255)) throw new InvalidDataException("Invalid squad number: " + val);
			p.SquadNumber = res;
			p.ContractDetailsPending = true;

		});



		// --- Personality ---

		RegisterField("Adaptability", new string[2] { "Adaptacja", "Przystosowanie" }, (PlayerRecord p) => p.Adaptability.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte res; if (byte.TryParse(val, out res)) p.Adaptability = Math.Min((byte)20, res);

		});

		RegisterField("Ambition", new string[1] { "Ambicja" }, (PlayerRecord p) => p.Ambition.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte res; if (byte.TryParse(val, out res)) p.Ambition = Math.Min((byte)20, res);

		});

		RegisterField("Controversy", new string[1] { "Kontrowersje" }, (PlayerRecord p) => p.Controversy.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte res; if (byte.TryParse(val, out res)) p.Controversy = Math.Min((byte)20, res);

		});

		RegisterField("Determination_Pers", new string[] { "Determination", "Determinacja", "DeterminacjaOsobista", "DetPers" }, (PlayerRecord p) => p.Determination.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte result;
			if (!byte.TryParse(val, out result) || result > 20)
				throw new InvalidDataException("Determination must be an integer from 0 to 20.");
			if (ppl != null)
			{
				if (p.T89Offset <= 0 || p.T89Offset > ppl.Length - 87)
					throw new InvalidDataException("Missing native player attribute record for determination.");
				ppl[p.T89Offset + 86] = result;
			}
			p.Determination = result;

		});

		RegisterField("Loyalty", new string[2] { "Loyality", "Lojalnosc" }, (PlayerRecord p) => p.Loyalty.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte res; if (byte.TryParse(val, out res)) p.Loyalty = Math.Min((byte)20, res);

		});

		RegisterField("Pressure", new string[2] { "Presja", "OdpornoscNaPresje" }, (PlayerRecord p) => p.Pressure.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte res; if (byte.TryParse(val, out res)) p.Pressure = Math.Min((byte)20, res);

		});

		RegisterField("Professionalism", new string[1] { "Profesjonalizm" }, (PlayerRecord p) => p.Professionalism.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte res; if (byte.TryParse(val, out res)) p.Professionalism = Math.Min((byte)20, res);

		});

		RegisterField("Sportsmanship", new string[2] { "FairPlay", "SportoweZachowanie" }, (PlayerRecord p) => p.Sportsmanship.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte res; if (byte.TryParse(val, out res)) p.Sportsmanship = Math.Min((byte)20, res);

		});

		RegisterField("Temperament", new string[1] { "Temperament" }, (PlayerRecord p) => p.Temperament.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte res; if (byte.TryParse(val, out res)) p.Temperament = Math.Min((byte)20, res);

		});



		// --- Preferred Moves (PPM) ---

		RegisterField("PreferredMoves", new string[3] { "PPM", "SpecialMoves", "ZagraniaSpecjalne" },

			(PlayerRecord p) => (p.PreferredMoves != null && p.PreferredMoves.Count > 0) ? string.Join(";", p.PreferredMoves.ToArray()) : "",

			(PlayerRecord p, byte[] ppl, string val) =>

			{

				if (p.PreferredMoves == null) p.PreferredMoves = new List<string>();

				else p.PreferredMoves.Clear();

				if (!string.IsNullOrEmpty(val))

				{

					string[] parts = val.Split(new char[] { ';', ',' }, StringSplitOptions.RemoveEmptyEntries);

					foreach (string pt in parts)

					{

						string trimmed = pt.Trim();

						if (!string.IsNullOrEmpty(trimmed) && !p.PreferredMoves.Contains(trimmed))

							p.PreferredMoves.Add(trimmed);

					}

				}

			});

		RegisterField("Height", new string[1] { "Wzrost" }, (PlayerRecord p) => p.Height.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			int result;

			if (int.TryParse(val, out result))

			{

				p.Height = result;

				if (ppl != null && p.PersonOffset > 0 && p.PersonOffset + 29 <= ppl.Length)

				{

					BitConverter.GetBytes((short)result).CopyTo(ppl, p.PersonOffset + 27);

				}

			}

		});

		RegisterField("Weight", new string[1] { "Waga" }, (PlayerRecord p) => p.Weight.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			int result;

			if (int.TryParse(val, out result))

			{

				p.Weight = result;

				if (ppl != null && p.PersonOffset > 0 && p.PersonOffset + 27 <= ppl.Length)

				{

					BitConverter.GetBytes((short)result).CopyTo(ppl, p.PersonOffset + 25);

				}

			}

		});

		RegisterField("LeftFoot", new string[2] { "LewaNoga", "FootLeft" }, (PlayerRecord p) => p.LeftFoot.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte result;

			if (byte.TryParse(val, out result))

			{

				if (result > 20)

				{

					result = 20;

				}

				p.LeftFoot = result;

				if (ppl != null && p.T89Offset > 0 && p.T89Offset + 59 < ppl.Length)

				{

					ppl[p.T89Offset + 59] = result;

				}

			}

		});

		RegisterField("RightFoot", new string[2] { "PrawaNoga", "FootRight" }, (PlayerRecord p) => p.RightFoot.ToString(), (PlayerRecord p, byte[] ppl, string val) =>

		{

			byte result;

			if (byte.TryParse(val, out result))

			{

				if (result > 20)

				{

					result = 20;

				}

				p.RightFoot = result;

				if (ppl != null && p.T89Offset > 0 && p.T89Offset + 60 < ppl.Length)

				{

					ppl[p.T89Offset + 60] = result;

				}

			}

		});

		RegisterT89PosField("GK", new string[2] { "Bramkarz", "Goalkeeper" }, 9, (PlayerRecord p) => p.PosGK, (PlayerRecord p, byte b) =>

		{

			p.PosGK = b;

		});

		RegisterT89PosField("SW", new string[2] { "Libero", "Sweeper" }, 10, (PlayerRecord p) => p.PosSW, (PlayerRecord p, byte b) =>

		{

			p.PosSW = b;

		});

		RegisterT89PosField("DL", new string[2] { "LewyObronca", "DefenderLeft" }, 21, (PlayerRecord p) => p.PosDL, (PlayerRecord p, byte b) =>

		{

			p.PosDL = b;

		});

		RegisterT89PosField("DC", new string[2] { "SrodkowyObronca", "DefenderCentral" }, 22, (PlayerRecord p) => p.PosDC, (PlayerRecord p, byte b) =>

		{

			p.PosDC = b;

		});

		RegisterT89PosField("DR", new string[2] { "PrawyObronca", "DefenderRight" }, 23, (PlayerRecord p) => p.PosDR, (PlayerRecord p, byte b) =>

		{

			p.PosDR = b;

		});

		RegisterT89PosField("DM", new string[2] { "DefensywnyPomocnik", "DefensiveMidfielder" }, 24, (PlayerRecord p) => p.PosDM, (PlayerRecord p, byte b) =>

		{

			p.PosDM = b;

		});

		RegisterT89PosField("ML", new string[2] { "LewyPomocnik", "MidfielderLeft" }, 25, (PlayerRecord p) => p.PosML, (PlayerRecord p, byte b) =>

		{

			p.PosML = b;

		});

		RegisterT89PosField("MC", new string[2] { "SrodkowyPomocnik", "MidfielderCentral" }, 26, (PlayerRecord p) => p.PosMC, (PlayerRecord p, byte b) =>

		{

			p.PosMC = b;

		});

		RegisterT89PosField("MR", new string[2] { "PrawyPomocnik", "MidfielderRight" }, 27, (PlayerRecord p) => p.PosMR, (PlayerRecord p, byte b) =>

		{

			p.PosMR = b;

		});

		RegisterT89PosField("AML", new string[3] { "OfensywnyPomocnikLewy", "AttackingMidLeft", "SkrzydlowyLewy" }, 28, (PlayerRecord p) => p.PosAML, (PlayerRecord p, byte b) =>

		{

			p.PosAML = b;

		});

		RegisterT89PosField("AMC", new string[2] { "OfensywnyPomocnikSrodkowy", "AttackingMidCentral" }, 29, (PlayerRecord p) => p.PosAMC, (PlayerRecord p, byte b) =>

		{

			p.PosAMC = b;

		});

		RegisterT89PosField("AMR", new string[3] { "OfensywnyPomocnikPrawy", "AttackingMidRight", "SkrzydlowyPrawy" }, 30, (PlayerRecord p) => p.PosAMR, (PlayerRecord p, byte b) =>

		{

			p.PosAMR = b;

		});

		RegisterT89PosField("ST", new string[4] { "Napastnik", "Striker", "FC", "Attacker" }, 31, (PlayerRecord p) => p.PosST, (PlayerRecord p, byte b) =>

		{

			p.PosST = b;

		});

		RegisterT89PosField("WBL", new string[2] { "LewyWahadlowy", "WingBackLeft" }, 32, (PlayerRecord p) => p.PosWBL, (PlayerRecord p, byte b) =>

		{

			p.PosWBL = b;

		});

		RegisterT89PosField("WBR", new string[2] { "PrawyWahadlowy", "WingBackRight" }, 33, (PlayerRecord p) => p.PosWBR, (PlayerRecord p, byte b) =>

		{

			p.PosWBR = b;

		});

		RegisterT89PosField("FreeRole", new string[1] { "WolnaRola" }, 17, (PlayerRecord p) => p.FreeRole, (PlayerRecord p, byte b) =>

		{

			p.FreeRole = b;

		});

		RegisterT89ByteField("Crossing", new string[2] { "Dosrodkowania", "Dośrodkowania" }, 34, (PlayerRecord p) => p.Crossing, (PlayerRecord p, byte b) =>

		{

			p.Crossing = b;

		});

		RegisterT89ByteField("Dribbling", new string[1] { "Drybling" }, 35, (PlayerRecord p) => p.Dribbling, (PlayerRecord p, byte b) =>

		{

			p.Dribbling = b;

		});

		RegisterT89ByteField("Finishing", new string[2] { "Wykonczenie", "Wykańczanie" }, 36, (PlayerRecord p) => p.Finishing, (PlayerRecord p, byte b) =>

		{

			p.Finishing = b;

		});

		RegisterT89ByteField("Heading", new string[2] { "GraGlowa", "GraGłową" }, 37, (PlayerRecord p) => p.Heading, (PlayerRecord p, byte b) =>

		{

			p.Heading = b;

		});

		RegisterT89ByteField("LongShots", new string[2] { "StrzalyZDystansu", "StrzałyZDystansu" }, 38, (PlayerRecord p) => p.LongShots, (PlayerRecord p, byte b) =>

		{

			p.LongShots = b;

		});

		RegisterT89ByteField("Marking", new string[1] { "Krycie" }, 39, (PlayerRecord p) => p.Marking, (PlayerRecord p, byte b) =>

		{

			p.Marking = b;

		});

		RegisterT89ByteField("OffTheBall", new string[3] { "Movement", "GraBezPilki", "GraBezPiłki" }, 40, (PlayerRecord p) => p.Movement, (PlayerRecord p, byte b) =>

		{

			p.Movement = b;

		});

		RegisterT89ByteField("Passing", new string[1] { "Podania" }, 41, (PlayerRecord p) => p.Passing, (PlayerRecord p, byte b) =>

		{

			p.Passing = b;

		});

		RegisterT89ByteField("Penalties", new string[2] { "RzutyKarne", "Karne" }, 42, (PlayerRecord p) => p.Penalties, (PlayerRecord p, byte b) =>

		{

			p.Penalties = b;

		});

		RegisterT89ByteField("Tackling", new string[1] { "Odbiory" }, 43, (PlayerRecord p) => p.Tackling, (PlayerRecord p, byte b) =>

		{

			p.Tackling = b;

		});

		RegisterT89ByteField("Creativity", new string[3] { "Kreatywnosc", "Kreatywność", "Vision" }, 44, (PlayerRecord p) => p.Creativity, (PlayerRecord p, byte b) =>

		{

			p.Creativity = b;

		});

		RegisterT89ByteField("FirstTouch", new string[2] { "PierwszeDotkniecie", "PierwszeDotknięcie" }, 57, (PlayerRecord p) => p.FirstTouch, (PlayerRecord p, byte b) =>

		{

			p.FirstTouch = b;

		});

		RegisterT89ByteField("Technique", new string[1] { "Technika" }, 58, (PlayerRecord p) => p.Technique, (PlayerRecord p, byte b) =>

		{

			p.Technique = b;

		});

		RegisterT89ByteField("Corners", new string[2] { "Rozne", "Rożne" }, 62, (PlayerRecord p) => p.Corners, (PlayerRecord p, byte b) =>

		{

			p.Corners = b;

		});

		RegisterT89ByteField("LongThrows", new string[2] { "DlugieWyrzuty", "DługieWyrzuty" }, 65, (PlayerRecord p) => p.LongThrows, (PlayerRecord p, byte b) =>

		{

			p.LongThrows = b;

		});

		RegisterT89ByteField("FreeKicks", new string[2] { "Wolne", "RzutyWolne" }, 70, (PlayerRecord p) => p.FreeKicks, (PlayerRecord p, byte b) =>

		{

			p.FreeKicks = b;

		});

		RegisterT89ByteField("Versatility", new string[2] { "Wszechstronnosc", "Wszechstronność" }, 84, (PlayerRecord p) => p.Versatility, (PlayerRecord p, byte b) =>

		{

			p.Versatility = b;

		});

		RegisterT89ByteField("Aggression", new string[1] { "Agresja" }, 80, (PlayerRecord p) => p.Aggression, (PlayerRecord p, byte b) =>

		{

			p.Aggression = b;

		});

		RegisterT89ByteField("Anticipation", new string[1] { "Antycypacja" }, 52, (PlayerRecord p) => p.Anticipation, (PlayerRecord p, byte b) =>

		{

			p.Anticipation = b;

		});

		RegisterT89ByteField("Bravery", new string[1] { "Odwaga" }, 78, (PlayerRecord p) => p.Bravery, (PlayerRecord p, byte b) =>

		{

			p.Bravery = b;

		});

		RegisterT89ByteField("Composure", new string[1] { "Opanowanie" }, 87, (PlayerRecord p) => p.Composure, (PlayerRecord p, byte b) =>

		{

			p.Composure = b;

		});

		RegisterT89ByteField("Concentration", new string[1] { "Koncentracja" }, 88, (PlayerRecord p) => p.Concentration, (PlayerRecord p, byte b) =>

		{

			p.Concentration = b;

		});

		RegisterT89ByteField("Consistency", new string[1] { "Konsekwencja" }, 79, (PlayerRecord p) => p.Consistency, (PlayerRecord p, byte b) =>

		{

			p.Consistency = b;

		});

		RegisterT89ByteField("Decisions", new string[1] { "Decyzje" }, 53, (PlayerRecord p) => p.Decisions, (PlayerRecord p, byte b) =>

		{

			p.Decisions = b;

		});

		RegisterT89ByteField("Dirtiness", new string[1] { "GraNaFaul" }, 76, (PlayerRecord p) => p.Dirtiness, (PlayerRecord p, byte b) =>

		{

			p.Dirtiness = b;

		});

		RegisterT89ByteField("Flair", new string[2] { "Blyskotliwosc", "Błyskotliwość" }, 61, (PlayerRecord p) => p.Flair, (PlayerRecord p, byte b) =>

		{

			p.Flair = b;

		});

		RegisterT89ByteField("ImportantMatches", new string[2] { "WazneMecze", "WażneMecze" }, 82, (PlayerRecord p) => p.ImportantMatches, (PlayerRecord p, byte b) =>

		{

			p.ImportantMatches = b;

		});

		RegisterT89ByteField("Leadership", new string[2] { "Przywodztwo", "Przywództwo" }, 75, (PlayerRecord p) => p.Leadership, (PlayerRecord p, byte b) =>

		{

			p.Leadership = b;

		});

		RegisterT89ByteField("Positioning", new string[2] { "UstawianieSie", "UstawianieSię" }, 55, (PlayerRecord p) => p.Positioning, (PlayerRecord p, byte b) =>

		{

			p.Positioning = b;

		});

		RegisterT89ByteField("Teamwork", new string[2] { "Wspolpraca", "Współpraca" }, 63, (PlayerRecord p) => p.Teamwork, (PlayerRecord p, byte b) =>

		{

			p.Teamwork = b;

		});

		RegisterT89ByteField("WorkRate", new string[2] { "Pracowitosc", "Pracowitość" }, 64, (PlayerRecord p) => p.WorkRate, (PlayerRecord p, byte b) =>

		{

			p.WorkRate = b;

		});

		RegisterT89ByteField("Acceleration", new string[1] { "Przyspieszenie" }, 69, (PlayerRecord p) => p.Acceleration, (PlayerRecord p, byte b) =>

		{

			p.Acceleration = b;

		});

		RegisterT89ByteField("Agility", new string[2] { "Zwinnosc", "Zwinność" }, 81, (PlayerRecord p) => p.Agility, (PlayerRecord p, byte b) =>

		{

			p.Agility = b;

		});

		RegisterT89ByteField("Balance", new string[2] { "Rownowaga", "Równowaga" }, 77, (PlayerRecord p) => p.Balance, (PlayerRecord p, byte b) =>

		{

			p.Balance = b;

		});

		RegisterT89ByteField("InjuryProneness", new string[2] { "PodatnoscNaKontuzje", "PodatnośćNaKontuzje" }, 83, (PlayerRecord p) => p.InjuryProneness, (PlayerRecord p, byte b) =>

		{

			p.InjuryProneness = b;

		});

		RegisterT89ByteField("Jumping", new string[2] { "Skocznosc", "Skoczność" }, 74, (PlayerRecord p) => p.Jumping, (PlayerRecord p, byte b) =>

		{

			p.Jumping = b;

		});

		RegisterT89ByteField("NaturalFitness", new string[2] { "SprawnoscOgolna", "SprawnośćOgólna" }, 85, (PlayerRecord p) => p.NaturalFitness, (PlayerRecord p, byte b) =>

		{

			p.NaturalFitness = b;

		});

		RegisterT89ByteField("Pace", new string[3] { "Szybkosc", "Szybkość", "Speed" }, 73, (PlayerRecord p) => p.Pace, (PlayerRecord p, byte b) =>

		{

			p.Pace = b;

		});

		RegisterT89ByteField("Stamina", new string[2] { "Wytrzymalosc", "Wytrzymałość" }, 72, (PlayerRecord p) => p.Stamina, (PlayerRecord p, byte b) =>

		{

			p.Stamina = b;

		});

		RegisterT89ByteField("Strength", new string[2] { "Sila", "Siła" }, 71, (PlayerRecord p) => p.Strength, (PlayerRecord p, byte b) =>

		{

			p.Strength = b;

		});

		RegisterT89ByteField("Handling", new string[1] { "Chwytanie" }, 45, (PlayerRecord p) => p.Handling, (PlayerRecord p, byte b) =>

		{

			p.Handling = b;

		});

		RegisterT89ByteField("AerialAbility", new string[1] { "GraWPowietrzu" }, 46, (PlayerRecord p) => p.AerialAbility, (PlayerRecord p, byte b) =>

		{

			p.AerialAbility = b;

		});

		RegisterT89ByteField("CommandOfArea", new string[1] { "Dowodzenie" }, 47, (PlayerRecord p) => p.CommandOfArea, (PlayerRecord p, byte b) =>

		{

			p.CommandOfArea = b;

		});

		RegisterT89ByteField("Communication", new string[1] { "Komunikacja" }, 48, (PlayerRecord p) => p.Communication, (PlayerRecord p, byte b) =>

		{

			p.Communication = b;

		});

		RegisterT89ByteField("Kicking", new string[1] { "Wykopy" }, 49, (PlayerRecord p) => p.Kicking, (PlayerRecord p, byte b) =>

		{

			p.Kicking = b;

		});

		RegisterT89ByteField("Throwing", new string[1] { "Wyrzuty" }, 50, (PlayerRecord p) => p.Throwing, (PlayerRecord p, byte b) =>

		{

			p.Throwing = b;

		});

		RegisterT89ByteField("OneOnOnes", new string[1] { "JedenNaJeden" }, 54, (PlayerRecord p) => p.OneOnOnes, (PlayerRecord p, byte b) =>

		{

			p.OneOnOnes = b;

		});

		RegisterT89ByteField("Reflexes", new string[1] { "Refleks" }, 56, (PlayerRecord p) => p.Reflexes, (PlayerRecord p, byte b) =>

		{

			p.Reflexes = b;

		});

		RegisterT89ByteField("Eccentricity", new string[2] { "Ekscentrycznosc", "Ekscentryczność" }, 66, (PlayerRecord p) => p.Eccentricity, (PlayerRecord p, byte b) =>

		{

			p.Eccentricity = b;

		});

		RegisterT89ByteField("RushingOut", new string[2] { "WyjsciaZBramki", "WyjściaZBramki" }, 67, (PlayerRecord p) => p.RushingOut, (PlayerRecord p, byte b) =>

		{

			p.RushingOut = b;

		});

		RegisterT89ByteField("TendencyToPunch", new string[2] { "Piastkowanie", "Piąstkowanie" }, 68, (PlayerRecord p) => p.TendencyToPunch, (PlayerRecord p, byte b) =>

		{

			p.TendencyToPunch = b;

		});

	}



	private void ExportToCsv(List<PlayerRecord> playersToExport)

	{

		if (playersToExport == null || playersToExport.Count == 0)

		{

			MessageBox.Show("Brak zawodników do wyeksportowania.", "Informacja", MessageBoxButtons.OK, MessageBoxIcon.Asterisk);

			return;

		}

		using (SaveFileDialog saveFileDialog = new SaveFileDialog())

		{

			saveFileDialog.Filter = "Pliki CSV (*.csv)|*.csv|Wszystkie pliki (*.*)|*.*";

			saveFileDialog.FileName = ((cbClubFilter != null && cbClubFilter.SelectedIndex > 1) ? ("sklad_" + SanitizeFileName(cbClubFilter.SelectedItem.ToString()) + ".csv") : "zawodnicy_fm08.csv");

			saveFileDialog.Title = "Wybierz lokalizację zapisu pliku CSV";

			if (saveFileDialog.ShowDialog() != DialogResult.OK)

			{

				return;

			}

			try

			{

				using (StreamWriter streamWriter = new StreamWriter(saveFileDialog.FileName, false, new UTF8Encoding(true)))

				{

					List<string> list = new List<string>();

					foreach (CsvField allCsvField in allCsvFields)

					{

						list.Add(EscapeCsv(allCsvField.HeaderName));

					}

					streamWriter.WriteLine(string.Join(",", list.ToArray()));

					foreach (PlayerRecord item in playersToExport)

					{

						List<string> list2 = new List<string>();

						foreach (CsvField allCsvField2 in allCsvFields)

						{

							string val = ((allCsvField2.Getter != null) ? allCsvField2.Getter(item) : "");

							list2.Add(EscapeCsv(val));

						}

						streamWriter.WriteLine(string.Join(",", list2.ToArray()));

					}

				}

				MessageBox.Show(string.Format("Pomyślnie wyeksportowano {0:N0} zawodników do pliku:\n{1}", playersToExport.Count, saveFileDialog.FileName), "Eksport CSV zakończony", MessageBoxButtons.OK, MessageBoxIcon.Asterisk);

			}

			catch (Exception ex)

			{

				MessageBox.Show("Błąd podczas eksportu do CSV:\n" + ex.Message, "Błąd", MessageBoxButtons.OK, MessageBoxIcon.Hand);

			}

		}

	}



	private void ImportFromCsv()

	{

		if (allPlayers == null || allPlayers.Count == 0 || loadedPeopleDbRaw == null)

		{

			MessageBox.Show("Najpierw wczytaj bazę danych FM 2008!", "Uwaga", MessageBoxButtons.OK, MessageBoxIcon.Exclamation);

			return;

		}

		using (OpenFileDialog openFileDialog = new OpenFileDialog())

		{

			openFileDialog.Filter = "Pliki CSV (*.csv;*.txt)|*.csv;*.txt|Wszystkie pliki (*.*)|*.*";

			openFileDialog.Title = "Wybierz plik CSV ze zmianami do zaimportowania";

			if (openFileDialog.ShowDialog() != DialogResult.OK)

			{

				return;

			}

			try

			{

				int num = 0;

				int num2 = 0;

				int addedCount = 0;

				Dictionary<int, PlayerRecord> dictionary = new Dictionary<int, PlayerRecord>();

				foreach (PlayerRecord allPlayer in allPlayers)

				{

					dictionary[allPlayer.Id] = allPlayer;

				}

				string[] array = File.ReadAllLines(openFileDialog.FileName, Encoding.UTF8);

				if (array.Length < 2)

				{

					MessageBox.Show("Plik CSV jest pusty lub zawiera tylko nagłówki.", "Błąd pliku", MessageBoxButtons.OK, MessageBoxIcon.Exclamation);

					return;

				}

				string[] array2 = ParseCsvLine(array[0]);

				CsvField[] array3 = new CsvField[array2.Length];

				int num3 = -1;

				int num4 = -1;

				int num5 = -1;

				int num6 = -1;

				for (int i = 0; i < array2.Length; i++)

				{

					string key = array2[i].Trim();

					CsvField value;

					if (csvFieldsByName.TryGetValue(key, out value))

					{

						array3[i] = value;

						if (value.Key.Equals("ID", StringComparison.OrdinalIgnoreCase))

						{

							num3 = i;

						}

						else if (value.Key.Equals("LastName", StringComparison.OrdinalIgnoreCase))

						{

							num4 = i;

						}

						else if (value.Key.Equals("FirstName", StringComparison.OrdinalIgnoreCase))

						{

							num5 = i;

						}

						else if (value.Key.Equals("Club", StringComparison.OrdinalIgnoreCase))

						{

							num6 = i;

						}

					}

				}

				for (int j = 1; j < array.Length; j++)

				{

					string text = array[j].Trim();

					if (string.IsNullOrEmpty(text))

					{

						continue;

					}

					string[] array4 = ParseCsvLine(text);

					PlayerRecord value2 = null;
					bool hasExplicitId = false;

					if (num3 != -1 && num3 < array4.Length)

					{

						string s = array4[num3].Trim();

						int result;

						if (int.TryParse(s, out result))

						{
							hasExplicitId = result > 0;

							dictionary.TryGetValue(result, out value2);

						}

					}

					if (value2 == null && !hasExplicitId && num4 != -1 && num4 < array4.Length)

					{

						string value3 = array4[num4].Trim();

						string value4 = ((num5 != -1 && num5 < array4.Length) ? array4[num5].Trim() : "");

						string value5 = ((num6 != -1 && num6 < array4.Length) ? array4[num6].Trim() : "");

						if (!string.IsNullOrEmpty(value3))

						{

							foreach (PlayerRecord allPlayer2 in allPlayers)

							{

								if (allPlayer2.LastName.Equals(value3, StringComparison.OrdinalIgnoreCase) && (string.IsNullOrEmpty(value4) || allPlayer2.FirstName.Equals(value4, StringComparison.OrdinalIgnoreCase)))

								{
									if (value2 != null) throw new InvalidDataException("Ambiguous player name in CSV; specify ID: " + value4 + " " + value3);

									value2 = allPlayer2;

								}

							}

						}

					}

					if (value2 == null)

					{

						string valLn = (num4 != -1 && num4 < array4.Length) ? array4[num4].Trim() : "";

						string valFn = (num5 != -1 && num5 < array4.Length) ? array4[num5].Trim() : "";

						if (!string.IsNullOrEmpty(valLn) || !string.IsNullOrEmpty(valFn))

						{

							int nextId = 0;

							if (num3 != -1 && num3 < array4.Length)

							{

								string idStr = array4[num3].Trim();

								int customId;

								if (int.TryParse(idStr, out customId) && customId > 0 && !dictionary.ContainsKey(customId))

								{

									nextId = customId;

								}

							}

							PlayerRecord newPlayer = CreateNewPlayer(nextId);

							for (int k = 0; k < array4.Length && k < array3.Length; k++)

							{

								if (k == num3) continue;

								CsvField csvField = array3[k];

								if (csvField != null && csvField.Setter != null)

								{

									string text2 = array4[k].Trim();

									if (text2.Length > 0)

									{

										csvField.Setter(newPlayer, null, text2);

									}

								}

							}

							AppendLoadedPlayer(newPlayer);
							newPlayer.IsModified = true;

							RefreshPlayerPositionString(newPlayer, loadedPeopleDbRaw);

							allPlayers.Add(newPlayer);

							dictionary[newPlayer.Id] = newPlayer;

							addedCount++;

						}

						else

						{

							num2++;

						}

						continue;

					}

					bool flag = false;

					for (int k = 0; k < array4.Length && k < array3.Length; k++)

					{

						if (k == num3)

						{

							continue;

						}

						CsvField csvField = array3[k];

						if (csvField != null && csvField.Setter != null)

						{

							string text2 = array4[k].Trim();

							if (text2.Length > 0)

							{

								csvField.Setter(value2, loadedPeopleDbRaw, text2);

								flag = true;

							}

						}

					}

					if (flag)

					{

						value2.IsModified = true;

						RefreshPlayerPositionString(value2, loadedPeopleDbRaw);

						num++;

					}

				}

				hasUnsavedChanges = true;

				gridPlayers.Refresh();

				if (gridPlayers.SelectedRows.Count > 0)

				{

					DisplayPlayerDetails((PlayerRecord)gridPlayers.SelectedRows[0].DataBoundItem);

				}

				ApplyFilter();

				lblStatus.Text = string.Format("Import zakończony: {0:N0} zaktualizowanych, {1:N0} nowo dodanych zawodników!", num, addedCount);

				MessageBox.Show(string.Format("Import z pliku CSV zakończony sukcesem!\n\n  -> Zaktualizowano istniejących zawodników: {0:N0}\n  -> DODANO NOWYCH ZAWODNIKÓW: {1:N0}\n  -> Pominięto pustych / niepoprawnych wierszy: {2:N0}\n\nŘącznie baza liczy teraz: {3:N0} zawodników.\nWprowadzone zmiany są widoczne w edytorze.\nPamiętaj, aby zapisać bazę danych ('Plik' -> 'Zapisz bazę danych jako...').", num, addedCount, num2, allPlayers.Count), "Wynik importu CSV", MessageBoxButtons.OK, MessageBoxIcon.Information);

			}

			catch (Exception ex)

			{

				MessageBox.Show("Błąd podczas przetwarzania pliku CSV:\n" + ex.Message, "Błąd", MessageBoxButtons.OK, MessageBoxIcon.Hand);

			}

		}

	}



	private void SaveDatabaseAs()

	{

		if (loadedPeopleDbRaw == null || string.IsNullOrEmpty(loadedDbPath))

		{

			MessageBox.Show("Najpierw wczytaj bazę danych, którą chcesz zapisać!", "Uwaga", MessageBoxButtons.OK, MessageBoxIcon.Exclamation);

			return;

		}

		using (FolderBrowserDialog folderBrowserDialog = new FolderBrowserDialog())

		{

			folderBrowserDialog.Description = "Wybierz folder docelowy dla nowej bazy danych (np. D:\\Gry\\FM08\\Dane\\db\\8.0.2 Extended 0.8):";

			folderBrowserDialog.SelectedPath = Path.GetDirectoryName(loadedDbPath);

			if (folderBrowserDialog.ShowDialog() != DialogResult.OK)

			{

				return;

			}

			string selectedPath = folderBrowserDialog.SelectedPath;

			if (selectedPath.Equals(loadedDbPath, StringComparison.OrdinalIgnoreCase))

			{

				DialogResult dialogResult = MessageBox.Show("Wybrałeś ten sam folder bazy, który jest aktualnie wczytany.\nCzy na pewno chcesz go nadpisać?", "Ostrzeżenie przed nadpisaniem", MessageBoxButtons.YesNo, MessageBoxIcon.Exclamation);

				if (dialogResult != DialogResult.Yes)

				{

					return;

				}

			}

			try

			{

				lblStatus.Text = "Zapisywanie bazy danych (kompresja Deflate + Adler32)...";

				Cursor = Cursors.WaitCursor;
				string sourceRoot = Path.GetFullPath(loadedDbPath).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
				string targetRoot = Path.GetFullPath(selectedPath).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
				if (!sourceRoot.Equals(targetRoot, StringComparison.OrdinalIgnoreCase) &&
					(sourceRoot.StartsWith(targetRoot, StringComparison.OrdinalIgnoreCase) || targetRoot.StartsWith(sourceRoot, StringComparison.OrdinalIgnoreCase)))
					throw new IOException("Folder docelowy nie może zawierać folderu źródłowego ani znajdować się wewnątrz niego.");
				SyncClubAssignments(ref loadedPeopleDbRaw, ref loadedServerDbRaw, allPlayers);
				loadedServerDbRaw = SyncRetirements(loadedServerDbRaw, allPlayers);

				if (!Directory.Exists(selectedPath))

				{

					Directory.CreateDirectory(selectedPath);

				}

				string[] files = Directory.GetFiles(loadedDbPath);

				string[] array = files;

				foreach (string text in array)

				{

					string fileName = Path.GetFileName(text);

					if (!Path.GetExtension(fileName).Equals(".xml", StringComparison.OrdinalIgnoreCase) && !fileName.Equals("people_db.dat", StringComparison.OrdinalIgnoreCase) && !fileName.Equals("server_db.dat", StringComparison.OrdinalIgnoreCase) && !(loadedClientDbRaw != null && fileName.Equals("client_db.dat", StringComparison.OrdinalIgnoreCase)))

					{

						string text2 = Path.Combine(selectedPath, fileName);

						if (!text2.Equals(text, StringComparison.OrdinalIgnoreCase))

						{

							File.Copy(text, text2, true);

						}

					}

				}

				if (!sourceRoot.Equals(targetRoot, StringComparison.OrdinalIgnoreCase))
					foreach (string directory in Directory.GetDirectories(loadedDbPath))
						foreach (string sourceFile in Directory.GetFiles(directory, "*", SearchOption.AllDirectories))
						{
							string destination = Path.Combine(selectedPath, sourceFile.Substring(sourceRoot.Length));
							Directory.CreateDirectory(Path.GetDirectoryName(destination));
							File.Copy(sourceFile, destination, true);
						}

				byte[] array2 = CompressFile(loadedPeopleDbRaw, loadedPeopleDbOrigHeader);

				string path = Path.Combine(selectedPath, "people_db.dat");



				File.WriteAllBytes(path, array2);
				if (loadedClientDbRaw != null)
					File.WriteAllBytes(Path.Combine(selectedPath, "client_db.dat"), CompressFile(loadedClientDbRaw, loadedClientDbOrigHeader));

				byte[] array3 = null;

				if (loadedServerDbRaw != null && loadedServerDbRaw.Length > 0)

				{

					array3 = CompressFile(loadedServerDbRaw, loadedServerDbOrigHeader);

					string path2 = Path.Combine(selectedPath, "server_db.dat");

					File.WriteAllBytes(path2, array3);

				}



				WriteDatabaseMetadata(loadedDbPath, selectedPath);
				hasUnsavedChanges = false;

				Cursor = Cursors.Default;

				lblStatus.Text = "Baza danych została pomyślnie zapisana!";

				DetectDatabases();

				string fileName2 = Path.GetFileName(selectedPath);

				if (cbDatabases.Items.Contains(fileName2))

				{

					cbDatabases.SelectedItem = fileName2;

				}

				MessageBox.Show(string.Format("Baza danych zapisana w folderze:\n{0}\n\npeople_db.dat: {1:N0} bajtow\nserver_db.dat: {2:N0} bajtow\n\nPrzed rozpoczeciem nowej gry WCZYTAJ i ZAPISZ te baze oficjalnym edytorem SI. Ten etap jest nadal wymagany po naszych zmianach.", selectedPath, array2.Length, (array3 != null ? array3.Length : 0)), "Zapis bazy - wymagany edytor SI", MessageBoxButtons.OK, MessageBoxIcon.Information);

			}

			catch (Exception ex)

			{

				Cursor = Cursors.Default;

				MessageBox.Show("Błąd podczas zapisywania bazy danych:\n" + ex.Message, "Błąd zapisu", MessageBoxButtons.OK, MessageBoxIcon.Hand);

				lblStatus.Text = "Błąd zapisu bazy danych.";

			}

		}

	}



	private void ClubCompetitionCsvDialog(bool import, bool european)
	{
		string title = european ? "Przydziały europejskich pucharów" : "Przydziały lig";
		if (loadedServerDbRaw == null || loadedPeopleDbRaw == null)
		{
			MessageBox.Show("Najpierw wczytaj bazę danych.", title, MessageBoxButtons.OK, MessageBoxIcon.Warning);
			return;
		}
		using (FileDialog dialog = import ? (FileDialog)new OpenFileDialog() : new SaveFileDialog())
		{
			dialog.Filter = title + " CSV (*.csv)|*.csv";
			dialog.Title = (import ? "Importuj: " : "Eksportuj: ") + title;
			if (!import) dialog.FileName = european ? "club_european_competitions.csv" : "club_leagues.csv";
			if (dialog.ShowDialog() != DialogResult.OK) return;
			try
			{
				Cursor = Cursors.WaitCursor;
				int personCount = BitConverter.ToInt32(loadedPeopleDbRaw, 0);
				if (import)
				{
					var changes = ReadClubCompetitionCsv(dialog.FileName, european);
					byte[] updated = ApplyClubCompetitionChanges(loadedServerDbRaw, personCount, changes, european);
					int changed = changes.Count(change => change.ExpectedCompetitionIndex != change.TargetCompetitionIndex);
					if (changed > 0)
					{
						loadedServerDbRaw = updated;
						hasUnsavedChanges = true;
					}
					lblStatus.Text = title + ": zmieniono " + changed + " klubów; liczebność rozgrywek zachowana.";
					MessageBox.Show(lblStatus.Text + (changed > 0 ? "\nZapisz bazę przez Plik → Zapisz bazę danych jako, a następnie wczytaj i zapisz ją w edytorze SI." : "\nBrak zmian do zapisania."),
						"Import: " + title, MessageBoxButtons.OK, MessageBoxIcon.Information);
				}
				else
				{
					ExportClubCompetitionCsv(dialog.FileName, loadedServerDbRaw, personCount, LoadedClubs, european);
					lblStatus.Text = "Wyeksportowano: " + title + ".";
					MessageBox.Show((european ? "Zmień TargetEuropeanCompetitionIndex, pozostawiając ExpectedEuropeanCompetitionIndex bez zmian." :
						"Zmień TargetDivisionIndex, pozostawiając ExpectedDivisionIndex bez zmian.") +
						"\nMożesz usunąć niezmieniane kluby. Każde rozgrywki muszą zachować liczbę uczestników.\nIndeks celu odczytasz z klubu, który obecnie w nich występuje." +
						(european ? "\n-1 oznacza brak pucharu. Import nie zmienia etapu ani zasad." : ""),
						"Eksport: " + title, MessageBoxButtons.OK, MessageBoxIcon.Information);
				}
			}
			catch (Exception ex)
			{
				lblStatus.Text = "Błąd " + (import ? "importu" : "eksportu") + ": " + title + ".";
				MessageBox.Show(ex.Message, lblStatus.Text, MessageBoxButtons.OK, MessageBoxIcon.Error);
			}
			finally { Cursor = Cursors.Default; }
		}
	}

	private MenuStrip CreateAppMenu()

	{

		MenuStrip menuStrip = new MenuStrip();

		ToolStripMenuItem toolStripMenuItem = new ToolStripMenuItem("&Plik");

		ToolStripMenuItem value = new ToolStripMenuItem("&Wczytaj bazę danych...", null, btnLoad_Click);

		ToolStripMenuItem value2 = new ToolStripMenuItem("&Zapisz bazę danych jako...", null, (object s, EventArgs e) =>

		{

			SaveDatabaseAs();

		});

		ToolStripMenuItem value3 = new ToolStripMenuItem("&Eksportuj do CSV...", null, (object s, EventArgs e) =>

		{

			ExportToCsv((filteredPlayers != null && filteredPlayers.Count > 0) ? filteredPlayers : allPlayers);

		});

		ToolStripMenuItem value4 = new ToolStripMenuItem("&Importuj z pliku CSV...", null, (object s, EventArgs e) =>

		{

			ImportFromCsv();

		});

		ToolStripMenuItem value5 = new ToolStripMenuItem("&Zakończ", null, (object s, EventArgs e) =>

		{

			Close();

		});

		toolStripMenuItem.DropDownItems.Add(value);

		toolStripMenuItem.DropDownItems.Add(value2);

		toolStripMenuItem.DropDownItems.Add(new ToolStripSeparator());

		toolStripMenuItem.DropDownItems.Add(value3);

		toolStripMenuItem.DropDownItems.Add(value4);

		toolStripMenuItem.DropDownItems.Add(new ToolStripSeparator());

		toolStripMenuItem.DropDownItems.Add(new ToolStripMenuItem("Eksportuj przydziały lig do CSV...", null, (s, e) => ClubCompetitionCsvDialog(false, false)));
		toolStripMenuItem.DropDownItems.Add(new ToolStripMenuItem("Importuj przydziały lig z CSV...", null, (s, e) => ClubCompetitionCsvDialog(true, false)));
		toolStripMenuItem.DropDownItems.Add(new ToolStripMenuItem("Eksportuj przydziały europejskich pucharów do CSV...", null, (s, e) => ClubCompetitionCsvDialog(false, true)));
		toolStripMenuItem.DropDownItems.Add(new ToolStripMenuItem("Importuj przydziały europejskich pucharów z CSV...", null, (s, e) => ClubCompetitionCsvDialog(true, true)));
		toolStripMenuItem.DropDownItems.Add(new ToolStripSeparator());

		toolStripMenuItem.DropDownItems.Add(value5);

		ToolStripMenuItem toolStripMenuItem2 = new ToolStripMenuItem("&Narzędzia");

		ToolStripMenuItem value6 = new ToolStripMenuItem("Otwórz folder baz danych", null, (object s, EventArgs e) =>

		{

			try

			{

				Process.Start("explorer.exe", "D:\\Gry\\FM08\\Dane\\db");

			}

			catch

			{

			}

		});

		ToolStripMenuItem value7 = new ToolStripMenuItem("Otwórz specyfikację CSV_SCHEMA.md", null, (object s, EventArgs e) =>

		{

			try

			{

				Process.Start("D:\\Gry\\FM08\\FMExt\\CSV_SCHEMA.md");

			}

			catch

			{

			}

		});

		toolStripMenuItem2.DropDownItems.Add(value6);

		toolStripMenuItem2.DropDownItems.Add(value7);

		ToolStripMenuItem menuEdit = new ToolStripMenuItem("&Edycja");

		ToolStripMenuItem itemAdd = new ToolStripMenuItem("&Dodaj nowego zawodnika...", null, (object s, EventArgs e) => this.AddNewPlayer());

		itemAdd.ShortcutKeys = Keys.Control | Keys.N;

		ToolStripMenuItem itemEdit = new ToolStripMenuItem("&Edytuj zaznaczonego zawodnika...", null, (object s, EventArgs e) =>

		{

			if (this.gridPlayers.SelectedRows.Count > 0)

			{

				this.ShowEditPlayerDialog((PlayerRecord)this.gridPlayers.SelectedRows[0].DataBoundItem);

			}

		});

		itemEdit.ShortcutKeys = Keys.Control | Keys.E;

		menuEdit.DropDownItems.Add(itemAdd);

		menuEdit.DropDownItems.Add(itemEdit);

		menuStrip.Items.Add(toolStripMenuItem);

		menuStrip.Items.Add(menuEdit);

		menuStrip.Items.Add(toolStripMenuItem2);

		return menuStrip;

	}



	public void AddNewPlayer()

	{

		if (allPlayers == null)

		{

			MessageBox.Show("Najpierw wczytaj bazę danych!", "Brak bazy", MessageBoxButtons.OK, MessageBoxIcon.Information);

			return;

		}

		PlayerRecord newPlayer = CreateNewPlayer(0);



		using (EditPlayerDialog dlg = new EditPlayerDialog(newPlayer, null, null, csvFieldsByName))

		{

			if (dlg.ShowDialog(this) == DialogResult.OK)

			{

				try { dlg.ApplyChanges(); AppendLoadedPlayer(newPlayer); }
				catch (Exception error)
				{
					MessageBox.Show(error.Message, "Player creation failed", MessageBoxButtons.OK, MessageBoxIcon.Error);
					return;
				}

				allPlayers.Add(newPlayer);

				if (filteredPlayers != null && filteredPlayers != allPlayers)

				{

					filteredPlayers.Insert(0, newPlayer);

				}

				hasUnsavedChanges = true;

				ApplyFilter();

				HighlightPlayer(newPlayer.Id);

				lblStatus.Text = string.Format("Dodano nowego zawodnika: {0} {1} (ID: {2})", newPlayer.FirstName, newPlayer.LastName, newPlayer.Id);

			}

		}

	}



	private void HighlightPlayer(int id)

	{

		if (gridPlayers == null || gridPlayers.Rows.Count == 0) return;

		for (int i = 0; i < gridPlayers.Rows.Count; i++)

		{

			PlayerRecord pr = gridPlayers.Rows[i].DataBoundItem as PlayerRecord;

			if (pr != null && pr.Id == id)

			{

				gridPlayers.ClearSelection();

				gridPlayers.Rows[i].Selected = true;

				gridPlayers.FirstDisplayedScrollingRowIndex = Math.Max(0, i - 2);

				DisplayPlayerDetails(pr);

				break;

			}

		}

	}



	private void ShowEditPlayerDialog(PlayerRecord p)

	{

		if (p == null)

		{

			return;

		}

		using (EditPlayerDialog dlg = new EditPlayerDialog(p, loadedPeopleDbRaw, loadedServerDbRaw, csvFieldsByName))

		{

			if (dlg.ShowDialog(this) == DialogResult.OK)

			{

				try
				{
					hasUnsavedChanges = true;
					dlg.ApplyChanges();
				}
				catch (Exception error)
				{
					MessageBox.Show(error.Message, "Player edit failed", MessageBoxButtons.OK, MessageBoxIcon.Error);
					return;
				}

				gridPlayers.Refresh();

				DisplayPlayerDetails(p);

				lblStatus.Text = "Zapisano zmiany zawodnika: " + p.FullName + " (ID: " + p.Id + "). Baza oczekuje na zapis!";

			}

		}

	}





	public class EditPlayerDialog : Form

	{

		private PlayerRecord player;

		private byte[] peopleDbRaw;

		private byte[] serverDbRaw;

		private Dictionary<string, CsvField> csvFields;

		private Dictionary<string, NumericUpDown> numControls = new Dictionary<string, NumericUpDown>();



		// Dynamic content panels

		private Panel pnlContentHost;

		private Panel pnlDetails;

		private Panel pnlContract;

		private Panel pnlPersonData;

		private Panel pnlPlayerData;

		private Panel pnlRelationships;



		// Navigation

		private TreeView treeSections;

		private ListBox lstRecentItems;

		private Label lblFooterStatus;



		// Details Controls

		private TextBox txtId;

		private TextBox txtFirstName;

		private TextBox txtLastName;

		private TextBox txtCommonName;

		private TextBox txtFullName;

		private ComboBox cbPersonType;

		private CheckBox chkFemale;

		private CheckBox chkBirthDate;

		private DateTimePicker dtpBirthDate;

		private CheckBox chkCity;

		private TextBox txtCity;

		private CheckBox chkNation;

		private TextBox txtNation;

		private CheckBox chkDeclaredForNation;

		private CheckBox chkIntRetirement;

		private ListBox lstSecondNations;

		private NumericUpDown numIntApps;

		private NumericUpDown numIntGoals;

		private NumericUpDown numU21Apps;

		private NumericUpDown numU21Goals;



		// Contract Controls (Club)

		private CheckBox chkClub;

		private TextBox txtClub;

		private ComboBox cbClubJob;

		private CheckBox chkDateJoined;

		private DateTimePicker dtpDateJoined;

		private CheckBox chkContractStarted;

		private DateTimePicker dtpContractStarted;

		private CheckBox chkContractExpires;

		private DateTimePicker dtpContractExpires;

		private CheckBox chkFullTime;

		private NumericUpDown numWeeklyWage;

		private CheckBox chkSquadNumber;

		private NumericUpDown numSquadNumber;

		private CheckBox chkCoownedBy;

		private TextBox txtCoownedBy;

		private NumericUpDown numCoownWage;



		// PPM checkboxes

		private List<CheckBox> ppmCheckBoxes = new List<CheckBox>();



		// Configurations

		private DataGridView dgvInjuries;

		private DataGridView dgvBans;

		private CheckBox chkRetirementDate;

		private DateTimePicker dtpRetirementDate;



		public EditPlayerDialog(PlayerRecord p, byte[] ppl, byte[] srv, Dictionary<string, CsvField> fields)

		{

			this.player = p;

			this.peopleDbRaw = ppl;

			this.serverDbRaw = srv;

			this.csvFields = fields;



			InitializeUI();

		}



		private void InitializeUI()

		{

			this.Text = "FM 2008 Data Editor v8.0.2 - " + player.FullName + " - Details";

			this.Size = new Size(1000, 720);

			this.MinimumSize = new Size(880, 620);

			this.StartPosition = FormStartPosition.CenterParent;

			this.Font = new Font("Segoe UI", 9f);

			this.BackColor = Color.FromArgb(240, 240, 240);



			// Pasek menu SI

			MenuStrip ms = new MenuStrip { BackColor = Color.FromArgb(245, 245, 245), Font = new Font("Segoe UI", 9f) };

			ToolStripMenuItem mnuFile = new ToolStripMenuItem("&File");

			ToolStripMenuItem mnuSave = new ToolStripMenuItem("&Save Record", null, (s, e) => { this.DialogResult = DialogResult.OK; this.Close(); });

			ToolStripMenuItem mnuClose = new ToolStripMenuItem("&Close", null, (s, e) => { this.DialogResult = DialogResult.Cancel; this.Close(); });

			mnuFile.DropDownItems.Add(mnuSave);

			mnuFile.DropDownItems.Add(new ToolStripSeparator());

			mnuFile.DropDownItems.Add(mnuClose);



			ToolStripMenuItem mnuEdit = new ToolStripMenuItem("&Edit");

			ToolStripMenuItem mnuHelp = new ToolStripMenuItem("&Help");

			ms.Items.Add(mnuFile);

			ms.Items.Add(mnuEdit);

			ms.Items.Add(mnuHelp);

			this.MainMenuStrip = ms;

			this.Controls.Add(ms);



			// Glowny SplitContainer (Lewy: Nawigacja 185px, Prawy: Tresc)

			SplitContainer splitMain = new SplitContainer

			{

				Dock = DockStyle.Fill,

				FixedPanel = FixedPanel.Panel1,

				SplitterDistance = 185,

				SplitterWidth = 4,

				BackColor = Color.FromArgb(220, 224, 230)

			};

			this.Controls.Add(splitMain);

			splitMain.BringToFront();



			// Panel dolny akcji (Save / Cancel)

			Panel pnlBottom = new Panel

			{

				Dock = DockStyle.Bottom,

				Height = 42,

				BackColor = Color.FromArgb(235, 238, 244),

				Padding = new Padding(10, 8, 10, 8)

			};

			this.Controls.Add(pnlBottom);

			pnlBottom.BringToFront();



			Button btnSave = new Button

			{

				Text = "Zapisz zmiany (OK)",

				DialogResult = DialogResult.OK,

				Anchor = AnchorStyles.Bottom | AnchorStyles.Right,

				Location = new Point(pnlBottom.Width - 280, 8),

				Size = new Size(150, 26),

				Font = new Font("Segoe UI", 9f, FontStyle.Bold),

				BackColor = Color.FromArgb(220, 235, 220),

				UseVisualStyleBackColor = false

			};

			btnSave.Click += (s, e) => { ApplyChanges(); };



			Button btnCancel = new Button

			{

				Text = "Anuluj",

				DialogResult = DialogResult.Cancel,

				Anchor = AnchorStyles.Bottom | AnchorStyles.Right,

				Location = new Point(pnlBottom.Width - 120, 8),

				Size = new Size(110, 26),

				Font = new Font("Segoe UI", 9f),

				UseVisualStyleBackColor = true

			};



			lblFooterStatus = new Label

			{

				Text = string.Format("Zawodnik: {0} (ID: {1})  |  CA: {2} / PA: {3}  |  Klub: {4}",

					player.FullName, player.Id, player.CA, player.PA, string.IsNullOrEmpty(player.Club) ? "Brak" : player.Club),

				Location = new Point(12, 12),

				AutoSize = true,

				Font = new Font("Segoe UI", 9f, FontStyle.Italic),

				ForeColor = Color.FromArgb(60, 60, 60)

			};



			pnlBottom.Controls.Add(btnSave);

			pnlBottom.Controls.Add(btnCancel);

			pnlBottom.Controls.Add(lblFooterStatus);



			// Budowanie Lewego Panelu (Sections na gorze, Recent Items na dole)

			BuildLeftNavigation(splitMain.Panel1);



			// Budowanie Prawego Panelu (Dynamiczne ekrany)

			BuildRightContent(splitMain.Panel2);



			// Domyslny wybor: Details

			if (treeSections.Nodes.Count > 0 && treeSections.Nodes[0].Nodes.Count > 0)

			{

				treeSections.SelectedNode = treeSections.Nodes[0].Nodes[0];

			}

		}



		private void BuildLeftNavigation(Panel parent)

		{

			// SplitContainer poziomy wewnatrz lewego panelu

			SplitContainer splitLeft = new SplitContainer

			{

				Dock = DockStyle.Fill,

				Orientation = Orientation.Horizontal,

				SplitterDistance = 380,

				SplitterWidth = 4,

				BackColor = Color.FromArgb(220, 224, 230)

			};

			parent.Controls.Add(splitLeft);



			// --- GORNY PANEL: Sections ---

			Panel pnlSections = splitLeft.Panel1;

			Label lblSectionsHeader = new Label

			{

				Text = "Sections",

				Dock = DockStyle.Top,

				Height = 22,

				TextAlign = ContentAlignment.MiddleCenter,

				Font = new Font("Segoe UI", 9f, FontStyle.Bold),

				BackColor = Color.FromArgb(235, 238, 244),

				BorderStyle = BorderStyle.FixedSingle

			};

			pnlSections.Controls.Add(lblSectionsHeader);



			treeSections = new TreeView

			{

				Dock = DockStyle.Fill,

				Font = new Font("Segoe UI", 9f),

				BorderStyle = BorderStyle.Fixed3D,

				HideSelection = false,

				ShowLines = true,

				ShowPlusMinus = true,

				ShowRootLines = true

			};



			TreeNode rootNode = new TreeNode(player.FullName);

			TreeNode nodeDetails = new TreeNode("Details");

			TreeNode nodeContract = new TreeNode("Contract");

			TreeNode nodePersonData = new TreeNode("Person Data");

			TreeNode nodePlayerData = new TreeNode("Player Data");

			TreeNode nodeRelationships = new TreeNode("Relationships");



			rootNode.Nodes.Add(nodeDetails);

			rootNode.Nodes.Add(nodeContract);

			rootNode.Nodes.Add(nodePersonData);

			rootNode.Nodes.Add(nodePlayerData);

			rootNode.Nodes.Add(nodeRelationships);



			treeSections.Nodes.Add(rootNode);

			rootNode.ExpandAll();

			pnlSections.Controls.Add(treeSections);

			treeSections.BringToFront();



			treeSections.AfterSelect += (s, e) =>

			{

				SwitchSection(e.Node.Text);

			};



			// --- DOLNY PANEL: Recent Items ---

			Panel pnlRecent = splitLeft.Panel2;

			Label lblRecentHeader = new Label

			{

				Text = "Recent Items",

				Dock = DockStyle.Top,

				Height = 22,

				TextAlign = ContentAlignment.MiddleCenter,

				Font = new Font("Segoe UI", 9f, FontStyle.Bold),

				BackColor = Color.FromArgb(235, 238, 244),

				BorderStyle = BorderStyle.FixedSingle

			};

			pnlRecent.Controls.Add(lblRecentHeader);



			Panel pnlRecentBtns = new Panel

			{

				Dock = DockStyle.Bottom,

				Height = 32,

				BackColor = Color.FromArgb(240, 240, 240),

				Padding = new Padding(2)

			};



			Button btnRemove = new Button { Text = "Remove", Location = new Point(4, 4), Size = new Size(82, 24), Font = new Font("Segoe UI", 8f) };

			Button btnRemoveAll = new Button { Text = "Remove All", Location = new Point(90, 4), Size = new Size(86, 24), Font = new Font("Segoe UI", 8f) };

			pnlRecentBtns.Controls.Add(btnRemove);

			pnlRecentBtns.Controls.Add(btnRemoveAll);

			pnlRecent.Controls.Add(pnlRecentBtns);



			lstRecentItems = new ListBox

			{

				Dock = DockStyle.Fill,

				Font = new Font("Segoe UI", 9f),

				BorderStyle = BorderStyle.Fixed3D

			};

			lstRecentItems.Items.Add("Search");

			lstRecentItems.Items.Add(player.FullName);

			lstRecentItems.SelectedIndex = 1;

			pnlRecent.Controls.Add(lstRecentItems);

			lstRecentItems.BringToFront();



			btnRemove.Click += (s, e) =>

			{

				if (lstRecentItems.SelectedIndex >= 0)

					lstRecentItems.Items.RemoveAt(lstRecentItems.SelectedIndex);

			};

			btnRemoveAll.Click += (s, e) =>

			{

				lstRecentItems.Items.Clear();

			};

		}



		private void BuildRightContent(Panel parent)

		{

			pnlContentHost = new Panel

			{

				Dock = DockStyle.Fill,

				BackColor = Color.White

			};

			parent.Controls.Add(pnlContentHost);



			// Utworzenie 5 ekranow glownych

			BuildDetailsPanel();

			BuildContractPanel();

			BuildPersonDataPanel();

			BuildPlayerDataPanel();

			BuildRelationshipsPanel();



			pnlContentHost.Controls.Add(pnlDetails);

			pnlContentHost.Controls.Add(pnlContract);

			pnlContentHost.Controls.Add(pnlPersonData);

			pnlContentHost.Controls.Add(pnlPlayerData);

			pnlContentHost.Controls.Add(pnlRelationships);

		}



		private void SwitchSection(string sectionName)

		{

			if (sectionName == player.FullName || sectionName == "Details")

			{

				pnlDetails.BringToFront();

				this.Text = "FM 2008 Data Editor v8.0.2 - " + player.FullName + " - Details";

			}

			else if (sectionName == "Contract")

			{

				pnlContract.BringToFront();

				this.Text = "FM 2008 Data Editor v8.0.2 - " + player.FullName + " - Contract";

			}

			else if (sectionName == "Person Data")

			{

				pnlPersonData.BringToFront();

				this.Text = "FM 2008 Data Editor v8.0.2 - " + player.FullName + " - Person Data";

			}

			else if (sectionName == "Player Data")

			{

				pnlPlayerData.BringToFront();

				this.Text = "FM 2008 Data Editor v8.0.2 - " + player.FullName + " - Player Data";

			}

			else if (sectionName == "Relationships")

			{

				pnlRelationships.BringToFront();

				this.Text = "FM 2008 Data Editor v8.0.2 - " + player.FullName + " - Relationships";

			}

		}



		// ==========================================

		// EKRAN 1: DETAILS (1:1 z PersonDetailsPanel.xrc)

		// ==========================================

		private void BuildDetailsPanel()

		{

			pnlDetails = new Panel { Dock = DockStyle.Fill, BackColor = Color.White, AutoScroll = true, Padding = new Padding(16) };



			Label lblTitle = new Label { Text = "Details", Location = new Point(16, 12), AutoSize = true, Font = new Font("Segoe UI", 10.5f, FontStyle.Bold) };

			pnlDetails.Controls.Add(lblTitle);



			int y = 42;

			int lblW = 150;

			int txtW = 550;



			// Unique ID

			pnlDetails.Controls.Add(new Label { Text = "Unique ID", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			txtId = new TextBox { Location = new Point(170, y), Size = new Size(txtW, 23), Text = player.Id.ToString(), ReadOnly = true, BackColor = Color.FromArgb(245, 245, 245) };

			pnlDetails.Controls.Add(txtId);

			y += 30;



			// First Name

			pnlDetails.Controls.Add(new Label { Text = "First Name", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			txtFirstName = new TextBox { Location = new Point(170, y), Size = new Size(txtW, 23), Text = player.FirstName ?? "" };

			pnlDetails.Controls.Add(txtFirstName);

			y += 30;



			// Second Name

			pnlDetails.Controls.Add(new Label { Text = "Second Name", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			txtLastName = new TextBox { Location = new Point(170, y), Size = new Size(txtW, 23), Text = player.LastName ?? "" };

			pnlDetails.Controls.Add(txtLastName);

			y += 30;



			// Common Name

			pnlDetails.Controls.Add(new Label { Text = "Common Name", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			txtCommonName = new TextBox { Location = new Point(170, y), Size = new Size(txtW, 23), Text = player.CommonName ?? "" };

			pnlDetails.Controls.Add(txtCommonName);

			y += 30;



			// Full Name

			pnlDetails.Controls.Add(new Label { Text = "Full Name", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			txtFullName = new TextBox { Location = new Point(170, y), Size = new Size(txtW, 23), Text = player.FullName ?? "" };

			pnlDetails.Controls.Add(txtFullName);

			y += 35;



			// Person Type

			pnlDetails.Controls.Add(new Label { Text = "Person Type", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			cbPersonType = new ComboBox { Location = new Point(170, y), Size = new Size(txtW, 23), DropDownStyle = ComboBoxStyle.DropDownList };

			cbPersonType.Items.AddRange(new string[] { "Player", "Non-Player", "Official" });

			cbPersonType.SelectedIndex = 0;

			pnlDetails.Controls.Add(cbPersonType);

			y += 30;



			// Female

			pnlDetails.Controls.Add(new Label { Text = "Female", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			chkFemale = new CheckBox { Location = new Point(170, y), Size = new Size(20, 20) };

			pnlDetails.Controls.Add(chkFemale);

			y += 32;



			// Date Of Birth

			pnlDetails.Controls.Add(new Label { Text = "Date Of Birth", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			chkBirthDate = new CheckBox { Location = new Point(170, y + 2), Size = new Size(20, 20), Checked = player.BirthDate.HasValue };

			dtpBirthDate = new DateTimePicker

			{

				Location = new Point(195, y),

				Size = new Size(txtW - 25, 23),

				Format = DateTimePickerFormat.Custom,

				CustomFormat = "dd.MM.yyyy",

				Value = (player.BirthDate.HasValue && player.BirthDate.Value.Year >= 1900) ? player.BirthDate.Value : new DateTime(1980, 1, 1),

				Enabled = player.BirthDate.HasValue

			};

			chkBirthDate.CheckedChanged += (s, e) => { dtpBirthDate.Enabled = chkBirthDate.Checked; };

			pnlDetails.Controls.Add(chkBirthDate);

			pnlDetails.Controls.Add(dtpBirthDate);

			y += 30;



			// City Of Birth

			pnlDetails.Controls.Add(new Label { Text = "City Of Birth", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			chkCity = new CheckBox { Location = new Point(170, y + 2), Size = new Size(20, 20), Checked = true };

			Button btnCityLookup = new Button { Text = "🔍", Location = new Point(195, y), Size = new Size(26, 23), Font = new Font("Segoe UI", 7.5f) };

			txtCity = new TextBox { Location = new Point(223, y), Size = new Size(txtW - 53, 23), Text = "Conegliano Veneto" };

			pnlDetails.Controls.Add(chkCity);

			pnlDetails.Controls.Add(btnCityLookup);

			pnlDetails.Controls.Add(txtCity);

			y += 30;



			// Nation

			pnlDetails.Controls.Add(new Label { Text = "Nation", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			chkNation = new CheckBox { Location = new Point(170, y + 2), Size = new Size(20, 20), Checked = !string.IsNullOrEmpty(player.Nationality) };

			Button btnNationLookup = new Button { Text = "🔍", Location = new Point(195, y), Size = new Size(26, 23), Font = new Font("Segoe UI", 7.5f) };

			txtNation = new TextBox { Location = new Point(223, y), Size = new Size(txtW - 53, 23), Text = player.Nationality ?? "" };

			btnNationLookup.Click += (s, e) => { ShowNationLookup(txtNation); };

			pnlDetails.Controls.Add(chkNation);

			pnlDetails.Controls.Add(btnNationLookup);

			pnlDetails.Controls.Add(txtNation);

			y += 30;



			// Declared For Nation

			pnlDetails.Controls.Add(new Label { Text = "Declared For Nation", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			chkDeclaredForNation = new CheckBox { Location = new Point(170, y + 2), Size = new Size(20, 20) };

			pnlDetails.Controls.Add(chkDeclaredForNation);

			y += 26;



			// International Retirement

			pnlDetails.Controls.Add(new Label { Text = "International Retirement", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			chkIntRetirement = new CheckBox { Location = new Point(170, y + 2), Size = new Size(20, 20) };

			pnlDetails.Controls.Add(chkIntRetirement);

			y += 28;



			// Second Nations

			pnlDetails.Controls.Add(new Label { Text = "Second Nations", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			lstSecondNations = new ListBox { Location = new Point(170, y), Size = new Size(460, 50), BorderStyle = BorderStyle.FixedSingle };

			Button btnAddSecNat = new Button { Text = "Add", Location = new Point(636, y), Size = new Size(84, 23) };

			Button btnRemSecNat = new Button { Text = "Remove", Location = new Point(636, y + 27), Size = new Size(84, 23) };

			btnAddSecNat.Click += (s, e) =>

			{

				using (UniversalSearchDialog dlg = new UniversalSearchDialog("Nation", new string[] { "Name" }))

				{

					if (FM08_Database_Editor.LoadedNations != null)

					{

						List<string[]> rows = new List<string[]>();

						foreach (string nat in FM08_Database_Editor.LoadedNations.Values) rows.Add(new string[] { nat });

						dlg.AddSampleData(rows.ToArray());

					}

					if (dlg.ShowDialog(this) == DialogResult.OK && !string.IsNullOrEmpty(dlg.SelectedValue))

					{

						if (!lstSecondNations.Items.Contains(dlg.SelectedValue)) lstSecondNations.Items.Add(dlg.SelectedValue);

					}

				}

			};

			btnRemSecNat.Click += (s, e) => { if (lstSecondNations.SelectedIndex >= 0) lstSecondNations.Items.RemoveAt(lstSecondNations.SelectedIndex); };

			pnlDetails.Controls.Add(lstSecondNations);

			pnlDetails.Controls.Add(btnAddSecNat);

			pnlDetails.Controls.Add(btnRemSecNat);

			y += 60;



			// International Apps & Goals

			pnlDetails.Controls.Add(new Label { Text = "International Apps", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			numIntApps = new NumericUpDown { Location = new Point(170, y), Size = new Size(txtW, 23), Minimum = 0, Maximum = 255, Value = player.InternationalApps };

			pnlDetails.Controls.Add(numIntApps);

			y += 28;



			pnlDetails.Controls.Add(new Label { Text = "International Goals", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			numIntGoals = new NumericUpDown { Location = new Point(170, y), Size = new Size(txtW, 23), Minimum = 0, Maximum = 255, Value = player.InternationalGoals };

			pnlDetails.Controls.Add(numIntGoals);

			y += 28;



			pnlDetails.Controls.Add(new Label { Text = "U21 International Apps", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			numU21Apps = new NumericUpDown { Location = new Point(170, y), Size = new Size(txtW, 23), Minimum = 0, Maximum = 255, Value = player.U21Apps };

			pnlDetails.Controls.Add(numU21Apps);

			y += 28;



			pnlDetails.Controls.Add(new Label { Text = "U21 International Goals", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			numU21Goals = new NumericUpDown { Location = new Point(170, y), Size = new Size(txtW, 23), Minimum = 0, Maximum = 100, Value = player.U21Goals };

			pnlDetails.Controls.Add(numU21Goals);

			y += 40;

		}



		// ==========================================

		// EKRAN 2: CONTRACT (4 Zakladki 1:1 z PersonContractPanel.xrc)

		// ==========================================

		private void BuildContractPanel()

		{

			pnlContract = new Panel { Dock = DockStyle.Fill, BackColor = Color.White };



			TabControl tabContract = new TabControl { Dock = DockStyle.Fill, Font = new Font("Segoe UI", 9f), Padding = new Point(12, 6) };

			TabPage tabClub = new TabPage("Club Contract") { BackColor = Color.White, AutoScroll = true };

			TabPage tabNation = new TabPage("Nation Contract") { BackColor = Color.White, AutoScroll = true };

			TabPage tabLoan = new TabPage("Loan") { BackColor = Color.White, AutoScroll = true };

			TabPage tabFuture = new TabPage("Future Transfer") { BackColor = Color.White, AutoScroll = true };



			tabContract.TabPages.Add(tabClub);

			tabContract.TabPages.Add(tabNation);

			tabContract.TabPages.Add(tabLoan);

			tabContract.TabPages.Add(tabFuture);

			pnlContract.Controls.Add(tabContract);



			// --- 1. Tab Club Contract ---

			int y = 14;

			int lblW = 150;

			int txtW = 550;



			// Club

			tabClub.Controls.Add(new Label { Text = "Club", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			chkClub = new CheckBox { Location = new Point(170, y + 2), Size = new Size(20, 20), Checked = !string.IsNullOrEmpty(player.Club) };

			Button btnClubLookup = new Button { Text = "🔍", Location = new Point(195, y), Size = new Size(26, 23), Font = new Font("Segoe UI", 7.5f) };

			txtClub = new TextBox { Location = new Point(223, y), Size = new Size(txtW - 53, 23), Text = player.Club ?? "" };

			btnClubLookup.Click += (s, e) => { ShowClubLookup(txtClub); };

			tabClub.Controls.Add(chkClub);

			tabClub.Controls.Add(btnClubLookup);

			tabClub.Controls.Add(txtClub);

			y += 30;



			// Job

			tabClub.Controls.Add(new Label { Text = "Job", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			cbClubJob = new ComboBox { Location = new Point(170, y), Size = new Size(txtW, 23), DropDownStyle = ComboBoxStyle.DropDownList };

			cbClubJob.Items.AddRange(new string[] { "Player", "Manager", "Assistant Manager", "Coach", "Physio", "Scout" });

			cbClubJob.SelectedIndex = 0;

			tabClub.Controls.Add(cbClubJob);

			y += 30;



			// Date Joined

			tabClub.Controls.Add(new Label { Text = "Date Joined", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			chkDateJoined = new CheckBox { Location = new Point(170, y + 2), Size = new Size(20, 20), Checked = true };

			dtpDateJoined = new DateTimePicker { Location = new Point(195, y), Size = new Size(txtW - 25, 23), Format = DateTimePickerFormat.Custom, CustomFormat = "dd.MM.yyyy", Value = new DateTime(2007, 7, 1) };

			tabClub.Controls.Add(chkDateJoined);

			tabClub.Controls.Add(dtpDateJoined);

			y += 30;



			// Contract Started

			tabClub.Controls.Add(new Label { Text = "Contract Started", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			chkContractStarted = new CheckBox { Location = new Point(170, y + 2), Size = new Size(20, 20), Checked = true };

			dtpContractStarted = new DateTimePicker { Location = new Point(195, y), Size = new Size(txtW - 25, 23), Format = DateTimePickerFormat.Custom, CustomFormat = "dd.MM.yyyy", Value = new DateTime(2007, 7, 1) };

			tabClub.Controls.Add(chkContractStarted);

			tabClub.Controls.Add(dtpContractStarted);

			y += 30;



			// Contract Expires

			tabClub.Controls.Add(new Label { Text = "Contract Expires", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			chkContractExpires = new CheckBox { Location = new Point(170, y + 2), Size = new Size(20, 20), Checked = player.ContractExpires.HasValue };

			dtpContractExpires = new DateTimePicker

			{

				Location = new Point(195, y),

				Size = new Size(txtW - 25, 23),

				Format = DateTimePickerFormat.Custom,

				CustomFormat = "dd.MM.yyyy",

				Value = (player.ContractExpires.HasValue && player.ContractExpires.Value.Year >= 1900) ? player.ContractExpires.Value : new DateTime(2010, 6, 30),

				Enabled = player.ContractExpires.HasValue

			};

			chkContractExpires.CheckedChanged += (s, e) => { dtpContractExpires.Enabled = chkContractExpires.Checked; };

			tabClub.Controls.Add(chkContractExpires);

			tabClub.Controls.Add(dtpContractExpires);

			y += 30;



			// Full Time Contract

			tabClub.Controls.Add(new Label { Text = "Full Time Contract", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			chkFullTime = new CheckBox { Location = new Point(170, y + 2), Size = new Size(20, 20), Checked = true };

			tabClub.Controls.Add(chkFullTime);

			y += 30;



			// Weekly Wage

			tabClub.Controls.Add(new Label { Text = "Weekly Wage", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			numWeeklyWage = new NumericUpDown { Location = new Point(170, y), Size = new Size(txtW, 23), Minimum = 0, Maximum = int.MaxValue, Value = player.WeeklyWage };

			tabClub.Controls.Add(numWeeklyWage);

			y += 30;



			// Squad Number

			tabClub.Controls.Add(new Label { Text = "Squad Number", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			chkSquadNumber = new CheckBox { Location = new Point(170, y + 2), Size = new Size(20, 20), Checked = (player.SquadNumber > 0 && player.SquadNumber <= 99) };

			numSquadNumber = new NumericUpDown { Location = new Point(195, y), Size = new Size(txtW - 25, 23), Minimum = 1, Maximum = 99, Value = (player.SquadNumber > 0 && player.SquadNumber <= 99 ? player.SquadNumber : 10) };

			tabClub.Controls.Add(chkSquadNumber);

			tabClub.Controls.Add(numSquadNumber);

			y += 35;



			// Coowned By

			tabClub.Controls.Add(new Label { Text = "Coowned By", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			chkCoownedBy = new CheckBox { Location = new Point(170, y + 2), Size = new Size(20, 20) };

			Button btnCoownLookup = new Button { Text = "🔍", Location = new Point(195, y), Size = new Size(26, 23), Font = new Font("Segoe UI", 7.5f) };

			txtCoownedBy = new TextBox { Location = new Point(223, y), Size = new Size(txtW - 53, 23), Text = "No Selection" };

			btnCoownLookup.Click += (s, e) => { ShowClubLookup(txtCoownedBy); };

			tabClub.Controls.Add(chkCoownedBy);

			tabClub.Controls.Add(btnCoownLookup);

			tabClub.Controls.Add(txtCoownedBy);

			y += 30;



			// Coown Wage

			tabClub.Controls.Add(new Label { Text = "Coown Wage", Location = new Point(16, y + 2), Size = new Size(lblW, 18) });

			numCoownWage = new NumericUpDown { Location = new Point(170, y), Size = new Size(txtW, 23), Minimum = 0, Maximum = 2000000000, Value = 0 };

			tabClub.Controls.Add(numCoownWage);

			y += 40;



			// Contract Clauses Box

			Label lblClauses = new Label { Text = "Contract Clauses", Location = new Point(16, y), AutoSize = true, Font = new Font("Segoe UI", 9f, FontStyle.Bold) };

			tabClub.Controls.Add(lblClauses);

			y += 24;



			// Clauses Kolumny 1 i 2

			int c1X = 16, c1ValX = 220;

			int c2X = 380, c2ValX = 580;

			int cy = y;



			AddClauseRow(tabClub, "Appearance Bonus", c1X, c1ValX, cy); cy += 28;

			AddClauseRow(tabClub, "Goal Bonus", c1X, c1ValX, cy); cy += 28;

			AddClauseRow(tabClub, "Promotion Wage Increase", c1X, c1ValX, cy); cy += 28;

			AddClauseRow(tabClub, "Relegation Wage Decrease", c1X, c1ValX, cy); cy += 28;

			AddClauseRow(tabClub, "Yearly Wage Increase", c1X, c1ValX, cy);



			cy = y;

			AddClauseRow(tabClub, "Minimum Fee Release", c2X, c2ValX, cy); cy += 28;

			AddClauseRow(tabClub, "Relegation Release Fee", c2X, c2ValX, cy); cy += 28;

			AddClauseRow(tabClub, "Non Promotion Release Fee", c2X, c2ValX, cy);



			// --- 2. Tab Nation Contract ---

			int ny = 14;

			tabNation.Controls.Add(new Label { Text = "Nation", Location = new Point(16, ny + 2), Size = new Size(lblW, 18) });

			tabNation.Controls.Add(new CheckBox { Location = new Point(170, ny + 2), Size = new Size(20, 20) });

			tabNation.Controls.Add(new Button { Text = "🔍", Location = new Point(195, ny), Size = new Size(26, 23), Font = new Font("Segoe UI", 7.5f) });

			tabNation.Controls.Add(new TextBox { Location = new Point(223, ny), Size = new Size(txtW - 53, 23), Text = "No Selection" });

			ny += 30;



			tabNation.Controls.Add(new Label { Text = "Job", Location = new Point(16, ny + 2), Size = new Size(lblW, 18) });

			tabNation.Controls.Add(new ComboBox { Location = new Point(170, ny), Size = new Size(txtW, 23), DropDownStyle = ComboBoxStyle.DropDownList });

			ny += 30;



			tabNation.Controls.Add(new Label { Text = "Date Joined", Location = new Point(16, ny + 2), Size = new Size(lblW, 18) });

			tabNation.Controls.Add(new CheckBox { Location = new Point(170, ny + 2), Size = new Size(20, 20), Checked = true });

			tabNation.Controls.Add(new DateTimePicker { Location = new Point(195, ny), Size = new Size(txtW - 25, 23), Format = DateTimePickerFormat.Custom, CustomFormat = "dd.MM.yyyy", Value = new DateTime(1991, 6, 1) });

			ny += 30;



			tabNation.Controls.Add(new Label { Text = "Contract Started", Location = new Point(16, ny + 2), Size = new Size(lblW, 18) });

			tabNation.Controls.Add(new CheckBox { Location = new Point(170, ny + 2), Size = new Size(20, 20) });

			tabNation.Controls.Add(new DateTimePicker { Location = new Point(195, ny), Size = new Size(txtW - 25, 23), Format = DateTimePickerFormat.Custom, CustomFormat = "dd.MM.yyyy", Value = new DateTime(1900, 1, 1), Enabled = false });

			ny += 30;



			tabNation.Controls.Add(new Label { Text = "Contract Expires", Location = new Point(16, ny + 2), Size = new Size(lblW, 18) });

			tabNation.Controls.Add(new CheckBox { Location = new Point(170, ny + 2), Size = new Size(20, 20) });

			tabNation.Controls.Add(new DateTimePicker { Location = new Point(195, ny), Size = new Size(txtW - 25, 23), Format = DateTimePickerFormat.Custom, CustomFormat = "dd.MM.yyyy", Value = new DateTime(1900, 1, 1), Enabled = false });

			ny += 30;



			tabNation.Controls.Add(new Label { Text = "Weekly Wage", Location = new Point(16, ny + 2), Size = new Size(lblW, 18) });

			tabNation.Controls.Add(new NumericUpDown { Location = new Point(170, ny), Size = new Size(txtW, 23), Minimum = 0, Maximum = 2000000000, Value = 0 });



			// --- 3. Tab Loan ---

			int ly = 14;

			tabLoan.Controls.Add(new Label { Text = "Club", Location = new Point(16, ly + 2), Size = new Size(lblW, 18) });

			tabLoan.Controls.Add(new CheckBox { Location = new Point(170, ly + 2), Size = new Size(20, 20) });

			tabLoan.Controls.Add(new Button { Text = "🔍", Location = new Point(195, ly), Size = new Size(26, 23), Font = new Font("Segoe UI", 7.5f) });

			tabLoan.Controls.Add(new TextBox { Location = new Point(223, ly), Size = new Size(txtW - 53, 23), Text = "No Selection" });

			ly += 30;

			tabLoan.Controls.Add(new Label { Text = "Start Date", Location = new Point(16, ly + 2), Size = new Size(lblW, 18) });

			tabLoan.Controls.Add(new CheckBox { Location = new Point(170, ly + 2), Size = new Size(20, 20) });

			tabLoan.Controls.Add(new DateTimePicker { Location = new Point(195, ly), Size = new Size(txtW - 25, 23), Format = DateTimePickerFormat.Custom, CustomFormat = "dd.MM.yyyy", Value = new DateTime(1900, 1, 1), Enabled = false });

			ly += 30;

			tabLoan.Controls.Add(new Label { Text = "End Date", Location = new Point(16, ly + 2), Size = new Size(lblW, 18) });

			tabLoan.Controls.Add(new CheckBox { Location = new Point(170, ly + 2), Size = new Size(20, 20) });

			tabLoan.Controls.Add(new DateTimePicker { Location = new Point(195, ly), Size = new Size(txtW - 25, 23), Format = DateTimePickerFormat.Custom, CustomFormat = "dd.MM.yyyy", Value = new DateTime(1900, 1, 1), Enabled = false });

			ly += 30;

			tabLoan.Controls.Add(new Label { Text = "Can Be Recalled", Location = new Point(16, ly + 2), Size = new Size(lblW, 18) });

			tabLoan.Controls.Add(new CheckBox { Location = new Point(170, ly + 2), Size = new Size(20, 20) });

			ly += 30;

			tabLoan.Controls.Add(new Label { Text = "Squad Number", Location = new Point(16, ly + 2), Size = new Size(lblW, 18) });

			tabLoan.Controls.Add(new CheckBox { Location = new Point(170, ly + 2), Size = new Size(20, 20) });

			tabLoan.Controls.Add(new NumericUpDown { Location = new Point(195, ly), Size = new Size(txtW - 25, 23), Minimum = 0, Maximum = 99, Value = 0, Enabled = false });

			ly += 30;

			tabLoan.Controls.Add(new Label { Text = "Fee To Buy", Location = new Point(16, ly + 2), Size = new Size(lblW, 18) });

			tabLoan.Controls.Add(new CheckBox { Location = new Point(170, ly + 2), Size = new Size(20, 20) });

			tabLoan.Controls.Add(new NumericUpDown { Location = new Point(195, ly), Size = new Size(txtW - 25, 23), Minimum = 0, Maximum = 2000000000, Value = 0, Enabled = false });

			ly += 30;

			tabLoan.Controls.Add(new Label { Text = "% Wages Paid By Loaning Club", Location = new Point(16, ly + 2), Size = new Size(lblW + 40, 18) });

			tabLoan.Controls.Add(new NumericUpDown { Location = new Point(220, ly), Size = new Size(txtW - 50, 23), Minimum = 0, Maximum = 100, Value = 0 });



			// --- 4. Tab Future Transfer ---

			int fy = 14;

			tabFuture.Controls.Add(new Label { Text = "Club", Location = new Point(16, fy + 2), Size = new Size(lblW, 18) });

			tabFuture.Controls.Add(new CheckBox { Location = new Point(170, fy + 2), Size = new Size(20, 20) });

			tabFuture.Controls.Add(new Button { Text = "🔍", Location = new Point(195, fy), Size = new Size(26, 23), Font = new Font("Segoe UI", 7.5f) });

			tabFuture.Controls.Add(new TextBox { Location = new Point(223, fy), Size = new Size(txtW - 53, 23), Text = "No Selection" });

			fy += 30;

			tabFuture.Controls.Add(new Label { Text = "Transfer Date", Location = new Point(16, fy + 2), Size = new Size(lblW, 18) });

			tabFuture.Controls.Add(new CheckBox { Location = new Point(170, fy + 2), Size = new Size(20, 20) });

			tabFuture.Controls.Add(new DateTimePicker { Location = new Point(195, fy), Size = new Size(txtW - 25, 23), Format = DateTimePickerFormat.Custom, CustomFormat = "dd.MM.yyyy", Value = new DateTime(1900, 1, 1), Enabled = false });

			fy += 30;

			tabFuture.Controls.Add(new Label { Text = "Contract End Date", Location = new Point(16, fy + 2), Size = new Size(lblW, 18) });

			tabFuture.Controls.Add(new CheckBox { Location = new Point(170, fy + 2), Size = new Size(20, 20) });

			tabFuture.Controls.Add(new DateTimePicker { Location = new Point(195, fy), Size = new Size(txtW - 25, 23), Format = DateTimePickerFormat.Custom, CustomFormat = "dd.MM.yyyy", Value = new DateTime(1900, 1, 1), Enabled = false });

			fy += 30;

			tabFuture.Controls.Add(new Label { Text = "Transfer Fee", Location = new Point(16, fy + 2), Size = new Size(lblW, 18) });

			tabFuture.Controls.Add(new CheckBox { Location = new Point(170, fy + 2), Size = new Size(20, 20) });

			tabFuture.Controls.Add(new NumericUpDown { Location = new Point(195, fy), Size = new Size(txtW - 25, 23), Minimum = 0, Maximum = 2000000000, Value = 0, Enabled = false });

			fy += 30;

			tabFuture.Controls.Add(new Label { Text = "Wage", Location = new Point(16, fy + 2), Size = new Size(lblW, 18) });

			tabFuture.Controls.Add(new CheckBox { Location = new Point(170, fy + 2), Size = new Size(20, 20) });

			tabFuture.Controls.Add(new NumericUpDown { Location = new Point(195, fy), Size = new Size(txtW - 25, 23), Minimum = 0, Maximum = 2000000000, Value = 0, Enabled = false });

			fy += 30;

			tabFuture.Controls.Add(new Label { Text = "New Job", Location = new Point(16, fy + 2), Size = new Size(lblW, 18) });

			tabFuture.Controls.Add(new CheckBox { Location = new Point(170, fy + 2), Size = new Size(20, 20) });

			tabFuture.Controls.Add(new ComboBox { Location = new Point(195, fy), Size = new Size(txtW - 25, 23), DropDownStyle = ComboBoxStyle.DropDownList, Enabled = false });

		}



		private void AddClauseRow(TabPage parent, string label, int lblX, int valX, int y)

		{

			parent.Controls.Add(new Label { Text = label, Location = new Point(lblX, y + 2), AutoSize = true });

			CheckBox chk = new CheckBox { Location = new Point(valX - 25, y + 2), Size = new Size(20, 20) };

			NumericUpDown num = new NumericUpDown { Location = new Point(valX, y), Size = new Size(110, 23), Minimum = 0, Maximum = 2000000000, Value = 0, Enabled = false };

			chk.CheckedChanged += (s, e) => { num.Enabled = chk.Checked; };

			parent.Controls.Add(chk);

			parent.Controls.Add(num);

		}



		// ==========================================

		// EKRAN 3: PERSON DATA (Attributes, Languages 1:1 z PersonDataPanel.xrc)

		// ==========================================

		private void BuildPersonDataPanel()

		{

			pnlPersonData = new Panel { Dock = DockStyle.Fill, BackColor = Color.White };



			TabControl tabPerson = new TabControl { Dock = DockStyle.Fill, Font = new Font("Segoe UI", 9f), Padding = new Point(12, 6) };

			TabPage tabAttr = new TabPage("Attributes") { BackColor = Color.White, AutoScroll = true, Padding = new Padding(12) };

			TabPage tabLang = new TabPage("Languages") { BackColor = Color.White, AutoScroll = true, Padding = new Padding(12) };



			tabPerson.TabPages.Add(tabAttr);

			tabPerson.TabPages.Add(tabLang);

			pnlPersonData.Controls.Add(tabPerson);



			// --- 1. Tab Attributes ---

			GroupBox grpPersonAttr = new GroupBox

			{

				Text = "Person Data Attributes",

				Location = new Point(20, 15),

				Size = new Size(240, 310),

				Font = new Font("Segoe UI", 9f)

			};

			int ay = 25;

			AddAttrSpin(grpPersonAttr, "Adaptability", "Adaptability", (player.Adaptability > 0 ? player.Adaptability : 10), 0, 20, ref ay);

			AddAttrSpin(grpPersonAttr, "Ambition", "Ambition", (player.Ambition > 0 ? player.Ambition : 12), 0, 20, ref ay);

			AddAttrSpin(grpPersonAttr, "Controversy", "Controversy", player.Controversy, 0, 20, ref ay);

			AddAttrSpin(grpPersonAttr, "Determination_Pers", "Determination", player.Determination, 0, 20, ref ay);

			AddAttrSpin(grpPersonAttr, "Loyalty", "Loyality", (player.Loyalty > 0 ? player.Loyalty : 10), 0, 20, ref ay);

			AddAttrSpin(grpPersonAttr, "Pressure", "Pressure", (player.Pressure > 0 ? player.Pressure : 12), 0, 20, ref ay);

			AddAttrSpin(grpPersonAttr, "Professionalism", "Professionalism", (player.Professionalism > 0 ? player.Professionalism : 12), 0, 20, ref ay);

			AddAttrSpin(grpPersonAttr, "Sportsmanship", "Sportsmanship", (player.Sportsmanship > 0 ? player.Sportsmanship : 12), 0, 20, ref ay);

			AddAttrSpin(grpPersonAttr, "Temperament", "Temperament", (player.Temperament > 0 ? player.Temperament : 12), 0, 20, ref ay);

			tabAttr.Controls.Add(grpPersonAttr);



			GroupBox grpJobPref = new GroupBox

			{

				Text = "Job Preferences",

				Location = new Point(280, 15),

				Size = new Size(240, 260),

				Font = new Font("Segoe UI", 9f)

			};

			int jy = 25;

			AddAttrSpin(grpJobPref, "JobPreferenceAssistantManager", "Assistant Manager", 0, 0, 20, ref jy);

			AddAttrSpin(grpJobPref, "JobPreferenceCoach", "Coach", 0, 0, 20, ref jy);

			AddAttrSpin(grpJobPref, "JobPreferenceFitnessCoach", "Fitness Coach", 0, 0, 20, ref jy);

			AddAttrSpin(grpJobPref, "JobPreferenceGoalkeepingCoach", "Goalkeeping Coach", 0, 0, 20, ref jy);

			AddAttrSpin(grpJobPref, "JobPreferenceManager", "Manager", 0, 0, 20, ref jy);

			AddAttrSpin(grpJobPref, "JobPreferencePhysio", "Physio", 0, 0, 20, ref jy);

			AddAttrSpin(grpJobPref, "JobPreferenceScout", "Scout", 0, 0, 20, ref jy);

			tabAttr.Controls.Add(grpJobPref);



			// --- 2. Tab Languages ---

			DataGridView dgvLang = new DataGridView

			{

				Location = new Point(16, 16),

				Size = new Size(680, 420),

				Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right,

				BackgroundColor = Color.White,

				RowHeadersVisible = false,

				AllowUserToAddRows = false,

				SelectionMode = DataGridViewSelectionMode.FullRowSelect,

				AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill

			};

			dgvLang.Columns.Add("chk", "");

			dgvLang.Columns[0].Width = 35;

			dgvLang.Columns.Add("lang", "Language");

			dgvLang.Columns[1].FillWeight = 60;

			dgvLang.Columns.Add("prof", "Proficiency");

			dgvLang.Columns[2].FillWeight = 40;



			dgvLang.Rows.Add(true, "Italian", "10");

			dgvLang.Rows.Add(true, "English", "7");



			Button btnAddLang = new Button { Text = "Add Language", Location = new Point(480, 445), Size = new Size(105, 26), Anchor = AnchorStyles.Bottom | AnchorStyles.Right };

			Button btnDelLang = new Button { Text = "Delete Selected", Location = new Point(590, 445), Size = new Size(105, 26), Anchor = AnchorStyles.Bottom | AnchorStyles.Right };

			btnAddLang.Click += (s, e) => { ShowLanguageSearchDialog(dgvLang); };

			btnDelLang.Click += (s, e) => { if (dgvLang.SelectedRows.Count > 0) dgvLang.Rows.RemoveAt(dgvLang.SelectedRows[0].Index); };



			tabLang.Controls.Add(dgvLang);

			tabLang.Controls.Add(btnAddLang);

			tabLang.Controls.Add(btnDelLang);

		}



		private void AddAttrSpin(GroupBox grp, string key, string label, int defVal, int min, int max, ref int y)

		{

			grp.Controls.Add(new Label { Text = label, Location = new Point(12, y + 2), Size = new Size(130, 18), AutoSize = false });

			NumericUpDown spin = new NumericUpDown { Location = new Point(155, y), Size = new Size(65, 23), Minimum = min, Maximum = max, Value = Math.Max(min, Math.Min(max, defVal)) };

			grp.Controls.Add(spin);

			numControls[key] = spin;

			y += 28;

		}



		// ==========================================

		// EKRAN 4: PLAYER DATA (6 Zakladek 1:1 z PlayerDataPanel.xrc)

		// ==========================================

		private void BuildPlayerDataPanel()

		{

			pnlPlayerData = new Panel { Dock = DockStyle.Fill, BackColor = Color.White };



			TabControl tabPlayer = new TabControl { Dock = DockStyle.Fill, Font = new Font("Segoe UI", 9f), Padding = new Point(10, 6) };

			TabPage tabRep = new TabPage("Reputation") { BackColor = Color.White, AutoScroll = true, Padding = new Padding(12) };

			TabPage tabPos = new TabPage("Positions") { BackColor = Color.White, AutoScroll = true, Padding = new Padding(12) };

			TabPage tabAttr1 = new TabPage("Attributes 1") { BackColor = Color.White, AutoScroll = true, Padding = new Padding(12) };

			TabPage tabAttr2 = new TabPage("Attributes 2") { BackColor = Color.White, AutoScroll = true, Padding = new Padding(12) };

			TabPage tabPpm = new TabPage("Preferred Moves") { BackColor = Color.White, AutoScroll = true, Padding = new Padding(12) };

			TabPage tabCfg = new TabPage("Configurations") { BackColor = Color.White, AutoScroll = true, Padding = new Padding(12) };



			tabPlayer.TabPages.Add(tabRep);

			tabPlayer.TabPages.Add(tabPos);

			tabPlayer.TabPages.Add(tabAttr1);

			tabPlayer.TabPages.Add(tabAttr2);

			tabPlayer.TabPages.Add(tabPpm);

			tabPlayer.TabPages.Add(tabCfg);

			pnlPlayerData.Controls.Add(tabPlayer);



			// --- 1. Tab Reputation ---

			GroupBox grpRep = new GroupBox { Text = "Ability & Reputation", Location = new Point(20, 15), Size = new Size(320, 200), Font = new Font("Segoe UI", 9f) };

			int ry = 25;

			AddAttrSpin(grpRep, "CA", "Playing Current Ability", player.CA, 0, 200, ref ry);

			AddAttrSpin(grpRep, "PA", "Playing Potential Ability", player.PA, -10, 200, ref ry);

			AddAttrSpin(grpRep, "CurrentReputation", "Playing Current Reputation", player.CurrentReputation, 0, 200, ref ry);

			AddAttrSpin(grpRep, "HomeReputation", "Playing Home Reputation", player.HomeReputation, 0, 200, ref ry);

			AddAttrSpin(grpRep, "WorldReputation", "Playing World Reputation", player.WorldReputation, 0, 200, ref ry);

			tabRep.Controls.Add(grpRep);



			// --- 2. Tab Positions (16 pozycji 1:1) ---

			GroupBox grpPos = new GroupBox { Text = "Positions", Location = new Point(20, 15), Size = new Size(420, 480), Font = new Font("Segoe UI", 9f) };

			int py = 25;

			AddAttrSpin(grpPos, "PosGK", "Goalkeeper", player.PosGK, 0, 20, ref py);

			AddAttrSpin(grpPos, "PosSW", "Sweeper", player.PosSW, 0, 20, ref py);

			AddAttrSpin(grpPos, "PosDL", "Defender Left Side", player.PosDL, 0, 20, ref py);

			AddAttrSpin(grpPos, "PosDC", "Defender Central", player.PosDC, 0, 20, ref py);

			AddAttrSpin(grpPos, "PosDR", "Defender Right Side", player.PosDR, 0, 20, ref py);

			AddAttrSpin(grpPos, "PosDM", "Defensive Midfielder Central", player.PosDM, 0, 20, ref py);

			AddAttrSpin(grpPos, "PosWBL", "Wing Back Left Side", player.PosWBL, 0, 20, ref py);

			AddAttrSpin(grpPos, "PosWBR", "Wing Back Right Side", player.PosWBR, 0, 20, ref py);

			AddAttrSpin(grpPos, "PosML", "Midfielder Left Side", player.PosML, 0, 20, ref py);

			AddAttrSpin(grpPos, "PosMC", "Midfielder Central", player.PosMC, 0, 20, ref py);

			AddAttrSpin(grpPos, "PosMR", "Midfielder Right Side", player.PosMR, 0, 20, ref py);

			AddAttrSpin(grpPos, "PosAML", "Attacking Midfielder Left Side", player.PosAML, 0, 20, ref py);

			AddAttrSpin(grpPos, "PosAMC", "Attacking Midfielder Central", player.PosAMC, 0, 20, ref py);

			AddAttrSpin(grpPos, "PosAMR", "Attacking Midfielder Right Side", player.PosAMR, 0, 20, ref py);

			AddAttrSpin(grpPos, "PosST", "Attacker Central", player.PosST, 0, 20, ref py);

			AddAttrSpin(grpPos, "FreeRole", "Free Role", player.FreeRole, 0, 20, ref py);

			tabPos.Controls.Add(grpPos);



			// --- 3. Tab Attributes 1 (Mental, Physical, Height/Weight) ---

			GroupBox grpMental = new GroupBox { Text = "Mental Attributes", Location = new Point(20, 15), Size = new Size(260, 480), Font = new Font("Segoe UI", 9f) };

			int my = 25;

			AddAttrSpin(grpMental, "Aggression", "Aggression", player.Aggression, 0, 20, ref my);

			AddAttrSpin(grpMental, "Anticipation", "Anticipation", player.Anticipation, 0, 20, ref my);

			AddAttrSpin(grpMental, "Bravery", "Bravery", player.Bravery, 0, 20, ref my);

			AddAttrSpin(grpMental, "Composure", "Composure", player.Composure, 0, 20, ref my);

			AddAttrSpin(grpMental, "Concentration", "Concentration", player.Concentration, 0, 20, ref my);

			AddAttrSpin(grpMental, "Consistency", "Consistency", player.Consistency, 0, 20, ref my);

			AddAttrSpin(grpMental, "Decisions", "Decisions", player.Decisions, 0, 20, ref my);

			AddAttrSpin(grpMental, "Dirtiness", "Dirtiness", player.Dirtiness, 0, 20, ref my);

			AddAttrSpin(grpMental, "Flair", "Flair", player.Flair, 0, 20, ref my);

			AddAttrSpin(grpMental, "ImportantMatches", "Important Matches", player.ImportantMatches, 0, 20, ref my);

			AddAttrSpin(grpMental, "Leadership", "Leadership", player.Leadership, 0, 20, ref my);

			AddAttrSpin(grpMental, "OffTheBall", "Off The Ball", player.Movement, 0, 20, ref my);

			AddAttrSpin(grpMental, "Positioning", "Positioning", player.Positioning, 0, 20, ref my);

			AddAttrSpin(grpMental, "Teamwork", "Teamwork", player.Teamwork, 0, 20, ref my);

			AddAttrSpin(grpMental, "Creativity", "Vision", player.Creativity, 0, 20, ref my);

			AddAttrSpin(grpMental, "WorkRate", "Work Rate", player.WorkRate, 0, 20, ref my);

			tabAttr1.Controls.Add(grpMental);



			GroupBox grpPhysical = new GroupBox { Text = "Physical Attributes", Location = new Point(300, 15), Size = new Size(260, 290), Font = new Font("Segoe UI", 9f) };

			int phy = 25;

			AddAttrSpin(grpPhysical, "Acceleration", "Acceleration", player.Acceleration, 0, 20, ref phy);

			AddAttrSpin(grpPhysical, "Agility", "Agility", player.Agility, 0, 20, ref phy);

			AddAttrSpin(grpPhysical, "Balance", "Balance", player.Balance, 0, 20, ref phy);

			AddAttrSpin(grpPhysical, "InjuryProneness", "Injury Proneness", player.InjuryProneness, 0, 20, ref phy);

			AddAttrSpin(grpPhysical, "Jumping", "Jumping", player.Jumping, 0, 20, ref phy);

			AddAttrSpin(grpPhysical, "NaturalFitness", "Natural Fitness", player.NaturalFitness, 0, 20, ref phy);

			AddAttrSpin(grpPhysical, "Pace", "Pace", player.Pace, 0, 20, ref phy);

			AddAttrSpin(grpPhysical, "Stamina", "Stamina", player.Stamina, 0, 20, ref phy);

			AddAttrSpin(grpPhysical, "Strength", "Strength", player.Strength, 0, 20, ref phy);

			tabAttr1.Controls.Add(grpPhysical);



			GroupBox grpHW = new GroupBox { Text = "Height & Weight", Location = new Point(300, 315), Size = new Size(260, 95), Font = new Font("Segoe UI", 9f) };

			int hwy = 25;

			AddAttrSpin(grpHW, "Height", "Height (cm)", player.Height, 0, 250, ref hwy);

			AddAttrSpin(grpHW, "Weight", "Weight (kg)", player.Weight, 0, 200, ref hwy);

			tabAttr1.Controls.Add(grpHW);



			// --- 4. Tab Attributes 2 (Technical, Goalkeeping, Foot) ---

			GroupBox grpTech = new GroupBox { Text = "Technical Attributes", Location = new Point(20, 15), Size = new Size(250, 460), Font = new Font("Segoe UI", 9f) };

			int ty = 25;

			AddAttrSpin(grpTech, "Corners", "Corners", player.Corners, 0, 20, ref ty);

			AddAttrSpin(grpTech, "Crossing", "Crossing", player.Crossing, 0, 20, ref ty);

			AddAttrSpin(grpTech, "Dribbling", "Dribbling", player.Dribbling, 0, 20, ref ty);

			AddAttrSpin(grpTech, "Finishing", "Finishing", player.Finishing, 0, 20, ref ty);

			AddAttrSpin(grpTech, "FirstTouch", "First Touch", player.FirstTouch, 0, 20, ref ty);

			AddAttrSpin(grpTech, "FreeKicks", "Free Kicks", player.FreeKicks, 0, 20, ref ty);

			AddAttrSpin(grpTech, "Heading", "Heading", player.Heading, 0, 20, ref ty);

			AddAttrSpin(grpTech, "LongShots", "Long Shots", player.LongShots, 0, 20, ref ty);

			AddAttrSpin(grpTech, "LongThrows", "Long Throws", player.LongThrows, 0, 20, ref ty);

			AddAttrSpin(grpTech, "Marking", "Marking", player.Marking, 0, 20, ref ty);

			AddAttrSpin(grpTech, "Passing", "Passing", player.Passing, 0, 20, ref ty);

			AddAttrSpin(grpTech, "Penalties", "Penalty Taking", player.Penalties, 0, 20, ref ty);

			AddAttrSpin(grpTech, "Tackling", "Tackling", player.Tackling, 0, 20, ref ty);

			AddAttrSpin(grpTech, "Technique", "Technique", player.Technique, 0, 20, ref ty);

			AddAttrSpin(grpTech, "Versatility", "Versatility", player.Versatility, 0, 20, ref ty);

			tabAttr2.Controls.Add(grpTech);



			GroupBox grpGK = new GroupBox { Text = "Goalkeeping Attributes", Location = new Point(290, 15), Size = new Size(250, 350), Font = new Font("Segoe UI", 9f) };

			int gky = 25;

			AddAttrSpin(grpGK, "AerialAbility", "Aerial Ability", player.AerialAbility, 0, 20, ref gky);

			AddAttrSpin(grpGK, "CommandOfArea", "Command Of Area", player.CommandOfArea, 0, 20, ref gky);

			AddAttrSpin(grpGK, "Communication", "Communication", player.Communication, 0, 20, ref gky);

			AddAttrSpin(grpGK, "Eccentricity", "Eccentricity", player.Eccentricity, 0, 20, ref gky);

			AddAttrSpin(grpGK, "Handling", "Handling", player.Handling, 0, 20, ref gky);

			AddAttrSpin(grpGK, "Kicking", "Kicking", player.Kicking, 0, 20, ref gky);

			AddAttrSpin(grpGK, "OneOnOnes", "One On Ones", player.OneOnOnes, 0, 20, ref gky);

			AddAttrSpin(grpGK, "Reflexes", "Reflexes", player.Reflexes, 0, 20, ref gky);

			AddAttrSpin(grpGK, "RushingOut", "Rushing Out", player.RushingOut, 0, 20, ref gky);

			AddAttrSpin(grpGK, "TendencyToPunch", "Tendency To Punch", player.TendencyToPunch, 0, 20, ref gky);

			AddAttrSpin(grpGK, "Throwing", "Throwing", player.Throwing, 0, 20, ref gky);

			tabAttr2.Controls.Add(grpGK);



			GroupBox grpFoot = new GroupBox { Text = "Preferred Foot", Location = new Point(290, 375), Size = new Size(250, 95), Font = new Font("Segoe UI", 9f) };

			int fty = 25;

			AddAttrSpin(grpFoot, "LeftFoot", "Left Foot", player.LeftFoot, 0, 20, ref fty);

			AddAttrSpin(grpFoot, "RightFoot", "Right Foot", player.RightFoot, 0, 20, ref fty);

			tabAttr2.Controls.Add(grpFoot);



			// --- 5. Tab Preferred Moves (PPM - 33 CheckBoxes 1:1) ---

			string[] ppmList = new string[]

			{

				"Runs With Ball Down Left",

				"Runs With Ball Down Right",

				"Runs With Ball Through The Center",

				"Gets Into Opposition Area",

				"Moves Into Channels",

				"Gets Forward Whenever Possible",

				"Plays Short Simple Passes",

				"Tries Killer Balls Often",

				"Shoots Long",

				"Shoots With Power",

				"Places Shots",

				"Curls Ball",

				"Likes To Round Keeper",

				"Likes To Try To Break Offside Trap",

				"Uses Outside Of Foot",

				"Marks Opponent Tightly",

				"Winds Up Opponents",

				"Argues With Officials",

				"Plays With Back To Goal",

				"Comes Deep To Get Ball",

				"Plays One Twos",

				"Likes To Lob Keeper",

				"Dictates Tempo",

				"Attempts Overhead Kicks",

				"Looks For Pass Not Shot",

				"Plays No Through Balls",

				"Stops Play",

				"Knocks Ball Past Opponent",

				"Moves Ball To Right Foot Before Dribble Attempt",

				"Moves Ball To Left Foot Before Dribble Attempt",

				"Dwells On Ball",

				"Arrives Late In Opposition Area",

				"Tries To Play Way Out Of Trouble"

			};



			Panel pnlPpmScroll = new Panel

			{

				Dock = DockStyle.Fill,

				AutoScroll = true,

				BackColor = Color.White,

				Padding = new Padding(12)

			};



			int ppmY = 12;

			foreach (string ppm in ppmList)

			{

				bool isPpmChecked = (player.PreferredMoves != null && player.PreferredMoves.Contains(ppm));

				CheckBox chkPpm = new CheckBox

				{

					Text = ppm,

					Location = new Point(16, ppmY),

					Size = new Size(380, 22),

					Font = new Font("Segoe UI", 9f),

					Checked = isPpmChecked

				};

				pnlPpmScroll.Controls.Add(chkPpm);

				ppmCheckBoxes.Add(chkPpm);

				ppmY += 24;

			}

			tabPpm.Controls.Add(pnlPpmScroll);



			// --- 6. Tab Configurations (Injuries, Bans, Retirement) ---

			// Injuries Box

			GroupBox grpInj = new GroupBox { Text = "Injuries", Location = new Point(16, 12), Size = new Size(720, 230), Font = new Font("Segoe UI", 9f) };

			dgvInjuries = new DataGridView

			{

				Location = new Point(12, 22),

				Size = new Size(696, 160),

				BackgroundColor = Color.White,

				RowHeadersVisible = false,

				AllowUserToAddRows = false,

				SelectionMode = DataGridViewSelectionMode.FullRowSelect,

				AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill

			};

			dgvInjuries.Columns.Add("inj", "Injury");

			dgvInjuries.Columns.Add("start", "Start Date");

			dgvInjuries.Columns.Add("end", "End Date");

			dgvInjuries.Columns.Add("future", "Future");

			dgvInjuries.Columns.Add("perm", "Permanent");

			dgvInjuries.Columns.Add("sev", "Severity");



			Button btnAddInj = new Button { Text = "Add Injury", Location = new Point(480, 190), Size = new Size(100, 26) };

			Button btnDelInj = new Button { Text = "Delete Selected Injuries", Location = new Point(585, 190), Size = new Size(123, 26) };



			btnAddInj.Click += (s, e) => { ShowInjurySearchDialog(); };

			btnDelInj.Click += (s, e) =>

			{

				if (dgvInjuries.SelectedRows.Count > 0)

					dgvInjuries.Rows.RemoveAt(dgvInjuries.SelectedRows[0].Index);

			};



			grpInj.Controls.Add(dgvInjuries);

			grpInj.Controls.Add(btnAddInj);

			grpInj.Controls.Add(btnDelInj);

			tabCfg.Controls.Add(grpInj);



			// Bans Box

			GroupBox grpBans = new GroupBox { Text = "Bans", Location = new Point(16, 250), Size = new Size(720, 180), Font = new Font("Segoe UI", 9f) };

			dgvBans = new DataGridView

			{

				Location = new Point(12, 22),

				Size = new Size(696, 115),

				BackgroundColor = Color.White,

				RowHeadersVisible = false,

				AllowUserToAddRows = false,

				SelectionMode = DataGridViewSelectionMode.FullRowSelect,

				AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill

			};

			dgvBans.Columns.Add("banType", "Ban Type");

			dgvBans.Columns.Add("endDate", "End Date");

			dgvBans.Columns.Add("numMatches", "Number Matches");



			Button btnAddBan = new Button { Text = "Add Ban", Location = new Point(480, 145), Size = new Size(100, 26) };

			Button btnDelBan = new Button { Text = "Delete Selected Bans", Location = new Point(585, 145), Size = new Size(123, 26) };

			btnAddBan.Click += (s, e) => { dgvBans.Rows.Add("Domestic Match Ban", DateTime.Now.AddMonths(1).ToString("dd.MM.yyyy"), "3"); };

			btnDelBan.Click += (s, e) => { if (dgvBans.SelectedRows.Count > 0) dgvBans.Rows.RemoveAt(dgvBans.SelectedRows[0].Index); };



			grpBans.Controls.Add(dgvBans);

			grpBans.Controls.Add(btnAddBan);

			grpBans.Controls.Add(btnDelBan);

			tabCfg.Controls.Add(grpBans);



			// Retirement Date

			Label lblRet = new Label { Text = "Retirement Date", Location = new Point(16, 445), AutoSize = true };

			chkRetirementDate = new CheckBox { Location = new Point(130, 443), Size = new Size(20, 20) };

			dtpRetirementDate = new DateTimePicker { Location = new Point(155, 441), Size = new Size(150, 23), Format = DateTimePickerFormat.Custom, CustomFormat = "dd.MM.yyyy", Value = new DateTime(1900, 1, 1), Enabled = false };

			chkRetirementDate.CheckedChanged += (s, e) => { dtpRetirementDate.Enabled = chkRetirementDate.Checked; };



			if (player.RetirementDate.HasValue)

			{

				chkRetirementDate.Checked = true;

				dtpRetirementDate.Value = player.RetirementDate.Value;

				dtpRetirementDate.Enabled = true;

			}

			else

			{

				chkRetirementDate.Checked = false;

				dtpRetirementDate.Value = new DateTime(2007, 7, 1);

				dtpRetirementDate.Enabled = false;

			}



			tabCfg.Controls.Add(lblRet);

			tabCfg.Controls.Add(chkRetirementDate);

			tabCfg.Controls.Add(dtpRetirementDate);

		}



		// ==========================================

		// EKRAN 5: RELATIONSHIPS (4 cwiartki 1:1 z PersonRelationshipPanel.xrc)

		// ==========================================

		private void BuildRelationshipsPanel()

		{

			pnlRelationships = new Panel { Dock = DockStyle.Fill, BackColor = Color.White, Padding = new Padding(12) };



			TableLayoutPanel tblRel = new TableLayoutPanel

			{

				Dock = DockStyle.Fill,

				ColumnCount = 2,

				RowCount = 2

			};

			tblRel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50f));

			tblRel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50f));

			tblRel.RowStyles.Add(new RowStyle(SizeType.Percent, 50f));

			tblRel.RowStyles.Add(new RowStyle(SizeType.Percent, 50f));



			tblRel.Controls.Add(CreateRelQuadrant("Favourite People", "Person", true), 0, 0);

			tblRel.Controls.Add(CreateRelQuadrant("Disliked People", "Person", true), 1, 0);

			tblRel.Controls.Add(CreateRelQuadrant("Favourite Clubs", "Club", false), 0, 1);

			tblRel.Controls.Add(CreateRelQuadrant("Disliked Clubs", "Club", false), 1, 1);



			pnlRelationships.Controls.Add(tblRel);

		}



		private GroupBox CreateRelQuadrant(string title, string entityName, bool isPerson)

		{

			GroupBox grp = new GroupBox { Text = title, Dock = DockStyle.Fill, Font = new Font("Segoe UI", 9f), Padding = new Padding(8) };

			DataGridView dgv = new DataGridView

			{

				Dock = DockStyle.Top,

				Height = 160,

				BackgroundColor = Color.White,

				RowHeadersVisible = false,

				AllowUserToAddRows = false,

				SelectionMode = DataGridViewSelectionMode.FullRowSelect,

				AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill

			};

			dgv.Columns.Add("ent", entityName);

			dgv.Columns.Add("lvl", "Level");

			dgv.Columns[1].Width = 70;



			// Przykladowe dane startowe dla Del Piero

			if (title == "Favourite Clubs" && player.Id == 8074)

			{

				dgv.Rows.Add("Juventus", "100");

			}

			else if (title == "Disliked Clubs" && player.Id == 8074)

			{

				dgv.Rows.Add("Inter", "85");

			}



			Panel pnlBtns = new Panel { Dock = DockStyle.Bottom, Height = 32 };

			Button btnAdd = new Button { Text = "Add", Location = new Point(pnlBtns.Width - 170, 4), Size = new Size(75, 24), Anchor = AnchorStyles.Bottom | AnchorStyles.Right };

			Button btnDel = new Button { Text = "Delete", Location = new Point(pnlBtns.Width - 90, 4), Size = new Size(75, 24), Anchor = AnchorStyles.Bottom | AnchorStyles.Right };



			btnAdd.Click += (s, e) =>

			{

				if (isPerson) ShowPersonSearchDialog(dgv);

				else ShowClubSearchDialog(dgv);

			};

			btnDel.Click += (s, e) => { if (dgv.SelectedRows.Count > 0) dgv.Rows.RemoveAt(dgv.SelectedRows[0].Index); };

			btnDel.Click += (s, e) =>

			{

				if (dgv.SelectedRows.Count > 0)

					dgv.Rows.RemoveAt(dgv.SelectedRows[0].Index);

			};



			pnlBtns.Controls.Add(btnAdd);

			pnlBtns.Controls.Add(btnDel);

			grp.Controls.Add(dgv);

			grp.Controls.Add(pnlBtns);

			return grp;

		}



		// ==========================================

		// DIALOGI WYSZUKIWANIA I FILTRY SI

		// ==========================================

		private void ShowInjurySearchDialog()

		{

			using (UniversalSearchDialog dlg = new UniversalSearchDialog("Injury", new string[] { "Name" }))

			{

				string[][] injuries = new string[][] {

					new string[] { "Torn Knee Ligaments" },

					new string[] { "Damaged Cruciate Ligaments" },

					new string[] { "Torn Calf Muscle" },

					new string[] { "Broken Leg" },

					new string[] { "Fractured Leg" },

					new string[] { "Fractured Skull" },

					new string[] { "Broken Ankle" },

					new string[] { "Damaged Achillies Tendon" },

					new string[] { "Hernia" },

					new string[] { "Dislocated Shoulder" },

					new string[] { "Groin Strain" },

					new string[] { "Hamstring Strain" },

					new string[] { "Thigh Strain" },

					new string[] { "Calf Strain" },

					new string[] { "Twisted Ankle" },

					new string[] { "Sprained Ankle" },

					new string[] { "Stubbed Toe" },

					new string[] { "Bruised Ribs" },

					new string[] { "Bruised Shin" },

					new string[] { "Bruised Jaw" },

					new string[] { "Facial Injury" },

					new string[] { "Broken Nose" },

					new string[] { "Concussion" },

					new string[] { "Back Strain" },

					new string[] { "Slipped Disc" },

					new string[] { "Chest Injury" },

					new string[] { "Lacerated Eye" },

					new string[] { "Gashed Leg" },

					new string[] { "Gashed Arm" },

					new string[] { "Fractured Metatarsal" },

					new string[] { "Fractured Arm" },

					new string[] { "Fractured Wrist" },

					new string[] { "Broken Collarbone" },

					new string[] { "Dislocated Jaw" },

					new string[] { "Whiplash" },

					new string[] { "Strained Neck" },

					new string[] { "Food Poisoning" },

					new string[] { "Influenza" },

					new string[] { "Viral Infection" },

					new string[] { "Cold" },

					new string[] { "Knee Cartilage Damage" },

					new string[] { "Hip Injury" },

					new string[] { "Sprained Wrist" },

					new string[] { "Dead Leg" },

					new string[] { "Tendonitis" },

					new string[] { "Shin Splints" },

					new string[] { "Pulled Hamstring" },

					new string[] { "Pulled Groin" }

				};

				dlg.AddSampleData(injuries);



				if (dlg.ShowDialog(this) == DialogResult.OK && !string.IsNullOrEmpty(dlg.SelectedValue))

				{

					dgvInjuries.Rows.Add(dlg.SelectedValue, DateTime.Now.ToString("dd.MM.yyyy"), DateTime.Now.AddMonths(1).ToString("dd.MM.yyyy"), false, false, 10);

				}

			}

		}



		private void ShowLanguageSearchDialog(DataGridView dgv)

		{

			using (UniversalSearchDialog dlg = new UniversalSearchDialog("Language", new string[] { "Language" }))

			{

				string[][] langs = new string[][] {

					new string[] { "English" }, new string[] { "Italian" }, new string[] { "Spanish" },

					new string[] { "French" }, new string[] { "German" }, new string[] { "Polish" },

					new string[] { "Portuguese" }, new string[] { "Dutch" }, new string[] { "Russian" },

					new string[] { "Turkish" }, new string[] { "Greek" }, new string[] { "Swedish" },

					new string[] { "Danish" }, new string[] { "Norwegian" }, new string[] { "Arabic" },

					new string[] { "Croatian" }, new string[] { "Serbian" }, new string[] { "Czech" },

					new string[] { "Slovak" }, new string[] { "Hungarian" }, new string[] { "Romanian" },

					new string[] { "Bulgarian" }, new string[] { "Japanese" }, new string[] { "Korean" },

					new string[] { "Chinese" }, new string[] { "Finnish" }, new string[] { "Ukrainian" }

				};

				dlg.AddSampleData(langs);

				if (dlg.ShowDialog(this) == DialogResult.OK && !string.IsNullOrEmpty(dlg.SelectedValue))

				{

					dgv.Rows.Add(true, dlg.SelectedValue, "10");

				}

			}

		}



		private void ShowClubLookup(TextBox target)

		{

			using (UniversalSearchDialog dlg = new UniversalSearchDialog("Club", new string[] { "Name" }))

			{

				if (FM08_Database_Editor.LoadedClubs != null && FM08_Database_Editor.LoadedClubs.Count > 0)

				{

					List<string[]> rows = new List<string[]>(FM08_Database_Editor.LoadedClubs.Count);

					foreach (var kvp in FM08_Database_Editor.LoadedClubs)

					{

						if (!string.IsNullOrEmpty(kvp.Value))

							rows.Add(new string[] { kvp.Value });

					}

					dlg.AddSampleData(rows.ToArray());

				}

				else

				{

					dlg.AddSampleData(new string[][] {

						new string[] { "Juventus" }, new string[] { "Milan" }, new string[] { "Inter" },

						new string[] { "Roma" }, new string[] { "Legia Warszawa" }, new string[] { "Wisla Krakow" },

						new string[] { "Barcelona" }, new string[] { "Real Madrid" }, new string[] { "Manchester United" },

						new string[] { "Arsenal" }, new string[] { "Chelsea" }, new string[] { "Liverpool" }

					});

				}



				if (dlg.ShowDialog(this) == DialogResult.OK && !string.IsNullOrEmpty(dlg.SelectedValue))

				{

					target.Text = dlg.SelectedValue;

					chkClub.Checked = true;

				}

			}

		}



		private void ShowNationLookup(TextBox target)

		{

			using (UniversalSearchDialog dlg = new UniversalSearchDialog("Nation", new string[] { "Name" }))

			{

				if (FM08_Database_Editor.LoadedNations != null && FM08_Database_Editor.LoadedNations.Count > 0)

				{

					List<string[]> rows = new List<string[]>(FM08_Database_Editor.LoadedNations.Count);

					foreach (var kvp in FM08_Database_Editor.LoadedNations)

					{

						if (!string.IsNullOrEmpty(kvp.Value))

							rows.Add(new string[] { kvp.Value });

					}

					dlg.AddSampleData(rows.ToArray());

				}

				else

				{

					dlg.AddSampleData(new string[][] {

						new string[] { "Italy" }, new string[] { "Poland" }, new string[] { "Brazil" },

						new string[] { "Argentina" }, new string[] { "France" }, new string[] { "Germany" },

						new string[] { "England" }, new string[] { "Spain" }, new string[] { "Netherlands" }

					});

				}



				if (dlg.ShowDialog(this) == DialogResult.OK && !string.IsNullOrEmpty(dlg.SelectedValue))

				{

					target.Text = dlg.SelectedValue;

					chkNation.Checked = true;

				}

			}

		}



		private void ShowClubSearchDialog(DataGridView dgv)

		{

			using (UniversalSearchDialog dlg = new UniversalSearchDialog("Club", new string[] { "Name" }))

			{

				if (FM08_Database_Editor.LoadedClubs != null && FM08_Database_Editor.LoadedClubs.Count > 0)

				{

					List<string[]> rows = new List<string[]>(FM08_Database_Editor.LoadedClubs.Count);

					foreach (var kvp in FM08_Database_Editor.LoadedClubs)

					{

						if (!string.IsNullOrEmpty(kvp.Value))

							rows.Add(new string[] { kvp.Value });

					}

					dlg.AddSampleData(rows.ToArray());

				}

				if (dlg.ShowDialog(this) == DialogResult.OK && !string.IsNullOrEmpty(dlg.SelectedValue))

				{

					dgv.Rows.Add(dlg.SelectedValue, "80");

				}

			}

		}



		private void ShowPersonSearchDialog(DataGridView dgv)

		{

			using (UniversalSearchDialog dlg = new UniversalSearchDialog("People", new string[] { "Name", "Nation", "Club", "Position" }))

			{

				if (FM08_Database_Editor.LoadedAllPlayers != null && FM08_Database_Editor.LoadedAllPlayers.Count > 0)

				{

					List<string[]> rows = new List<string[]>(FM08_Database_Editor.LoadedAllPlayers.Count);

					foreach (var pl in FM08_Database_Editor.LoadedAllPlayers)

					{

						rows.Add(new string[] {

							pl.FullName,

							string.IsNullOrEmpty(pl.Nationality) ? "-" : pl.Nationality,

							string.IsNullOrEmpty(pl.Club) ? "-" : pl.Club,

							string.IsNullOrEmpty(pl.Position) ? "-" : pl.Position

						});

					}

					dlg.AddSampleData(rows.ToArray());

				}

				else

				{

					dlg.AddSampleData(new string[][] {

						new string[] { "Buffon, Gianluigi", "Italy", "Juventus", "GK" },

						new string[] { "Nedved, Pavel", "Czech Republic", "Juventus", "AM LC" },

						new string[] { "Trezeguet, David", "France", "Juventus", "ST" },

						new string[] { "Lippi, Marcello", "Italy", "None", "Manager" }

					});

				}

				if (dlg.ShowDialog(this) == DialogResult.OK && !string.IsNullOrEmpty(dlg.SelectedValue))

				{

					dgv.Rows.Add(dlg.SelectedValue, "85");

				}

			}

		}



		// ==========================================

		// ZAPIS ZMIAN DO BAZY I MODELU

		// ==========================================

		public void ApplyChanges()

		{
			ResolveClubAssignment(txtClub != null && chkClub.Checked ? txtClub.Text.Trim() : "");
			if (chkRetirementDate != null && chkRetirementDate.Checked && (dtpRetirementDate.Value.Year < 1900 || dtpRetirementDate.Value.Year > 2100))
				throw new InvalidDataException("Retirement year must be between 1900 and 2100.");

			// 1. Zapis numerycznych cech zarejestrowanych w numControls

			foreach (KeyValuePair<string, NumericUpDown> kvp in numControls)

			{

				string fieldKey = kvp.Key;

				NumericUpDown num = kvp.Value;

				CsvField field;

				if (csvFields.TryGetValue(fieldKey, out field) && field.Setter != null)

				{

					field.Setter(player, peopleDbRaw, num.Value.ToString(CultureInfo.InvariantCulture));

				}

			}



			// 2. Zapis pol tekstowych i dat

			string newFn = (txtFirstName != null) ? txtFirstName.Text.Trim() : player.FirstName;

			string newLn = (txtLastName != null) ? txtLastName.Text.Trim() : player.LastName;

			FM08_Database_Editor.UpdatePlayerName(player, peopleDbRaw, serverDbRaw, newFn, newLn);



			if (txtCommonName != null)

			{

				FM08_Database_Editor.UpdatePlayerCommonName(player, peopleDbRaw, txtCommonName.Text.Trim());

			}

			string newNation = (txtNation != null && chkNation.Checked) ? txtNation.Text.Trim() : player.Nationality;

			FM08_Database_Editor.UpdatePlayerNation(player, peopleDbRaw, newNation);



			string newClub = (txtClub != null && chkClub.Checked) ? txtClub.Text.Trim() : "";

			FM08_Database_Editor.UpdatePlayerClub(player, peopleDbRaw, newClub);



			if (chkBirthDate != null && chkBirthDate.Checked)

			{

				FM08_Database_Editor.UpdatePlayerBirthDate(player, peopleDbRaw, dtpBirthDate.Value);

			}

			if (chkContractExpires != null && chkContractExpires.Checked)

			{

				FM08_Database_Editor.UpdatePlayerContract(player, peopleDbRaw, dtpContractExpires.Value);

			}

			if (chkRetirementDate != null)

			{

				csvFields["RetirementDate"].Setter(player, null, chkRetirementDate.Checked ? dtpRetirementDate.Value.ToString("dd.MM.yyyy", CultureInfo.InvariantCulture) : "CLEAR");

			}



			if (numIntApps != null) player.InternationalApps = (byte)numIntApps.Value;

			if (numIntGoals != null) player.InternationalGoals = (byte)numIntGoals.Value;

			if (numU21Apps != null) player.U21Apps = (byte)numU21Apps.Value;

			if (numU21Goals != null) player.U21Goals = (byte)numU21Goals.Value;

			if (numWeeklyWage != null && player.WeeklyWage != (int)numWeeklyWage.Value)
				csvFields["WeeklyWage"].Setter(player, null, numWeeklyWage.Value.ToString(CultureInfo.InvariantCulture));

			if (numSquadNumber != null)
			{
				byte number = chkSquadNumber.Checked ? (byte)numSquadNumber.Value : (byte)255;
				if (player.SquadNumber != number) csvFields["SquadNumber"].Setter(player, null, number.ToString(CultureInfo.InvariantCulture));
			}



			// Personality

			if (numControls.ContainsKey("Adaptability")) player.Adaptability = (byte)numControls["Adaptability"].Value;

			if (numControls.ContainsKey("Ambition")) player.Ambition = (byte)numControls["Ambition"].Value;

			if (numControls.ContainsKey("Controversy")) player.Controversy = (byte)numControls["Controversy"].Value;

			if (numControls.ContainsKey("Determination_Pers")) player.Determination = (byte)numControls["Determination_Pers"].Value;

			if (numControls.ContainsKey("Loyalty")) player.Loyalty = (byte)numControls["Loyalty"].Value;

			if (numControls.ContainsKey("Pressure")) player.Pressure = (byte)numControls["Pressure"].Value;

			if (numControls.ContainsKey("Professionalism")) player.Professionalism = (byte)numControls["Professionalism"].Value;

			if (numControls.ContainsKey("Sportsmanship")) player.Sportsmanship = (byte)numControls["Sportsmanship"].Value;

			if (numControls.ContainsKey("Temperament")) player.Temperament = (byte)numControls["Temperament"].Value;



			// Preferred Moves (PPM)

			if (player.PreferredMoves == null) player.PreferredMoves = new List<string>();

			else player.PreferredMoves.Clear();

			foreach (CheckBox chk in ppmCheckBoxes)

			{

				if (chk.Checked) player.PreferredMoves.Add(chk.Text);

			}



			// 3. Formatowanie pozycji

			player.Position = FM08_Database_Editor.FormatPosition(

				player.PosGK, player.PosSW, player.PosDL, player.PosDC, player.PosDR,

				player.PosDM, player.PosML, player.PosMC, player.PosMR,

				player.PosAML, player.PosAMC, player.PosAMR, player.PosST,

				player.PosWBL, player.PosWBR);



			player.IsModified = true;

		}

	}



	// ==========================================

	// UNIWERSALNY DIALOG WYSZUKIWANIA SI (SearchDialog.xrc + EditorColumns.xml)

	// ==========================================

	public class UniversalSearchDialog : Form

	{

		private string entityType;

		private TextBox txtFilter;

		private ListView lvResults;

		private Button btnFilter;

		private Button btnOk;

		private Button btnCancel;

		private List<string[]> allItems = new List<string[]>();



		public string SelectedValue { get; private set; }



		public UniversalSearchDialog(string entityType, string[] columnHeaders)

		{

			this.entityType = entityType;

			this.Text = "Search";

			this.Size = new Size(520, 560);

			this.StartPosition = FormStartPosition.CenterParent;

			this.Font = new Font("Segoe UI", 9f);

			this.FormBorderStyle = FormBorderStyle.FixedDialog;

			this.MaximizeBox = false;

			this.MinimizeBox = false;



			btnFilter = new Button { Text = "Filter", Location = new Point(12, 12), Size = new Size(65, 24) };

			btnFilter.Click += (s, e) =>

			{

				if (entityType == "Injury")

				{

					using (InjuryFilterDialog idlg = new InjuryFilterDialog())

					{

						idlg.ShowDialog(this);

					}

				}

				else

				{

					MessageBox.Show("Filtrowanie zaawansowane dla typu: " + entityType, "Filter", MessageBoxButtons.OK, MessageBoxIcon.Information);

				}

			};

			this.Controls.Add(btnFilter);



			txtFilter = new TextBox { Location = new Point(85, 13), Size = new Size(405, 23) };

			txtFilter.TextChanged += (s, e) => { FilterList(); };

			this.Controls.Add(txtFilter);



			lvResults = new ListView

			{

				Location = new Point(12, 45),

				Size = new Size(478, 430),

				View = View.Details,

				FullRowSelect = true,

				GridLines = true,

				MultiSelect = false

			};



			foreach (string h in columnHeaders)

			{

				lvResults.Columns.Add(h, 150);

			}

			if (lvResults.Columns.Count > 0)

			{

				lvResults.Columns[0].Width = 180;

			}

			lvResults.DoubleClick += (s, e) =>

			{

				if (lvResults.SelectedItems.Count > 0)

				{

					SelectedValue = lvResults.SelectedItems[0].Text;

					this.DialogResult = DialogResult.OK;

					this.Close();

				}

			};

			this.Controls.Add(lvResults);



			btnOk = new Button { Text = "OK", DialogResult = DialogResult.OK, Location = new Point(140, 485), Size = new Size(100, 26) };

			btnCancel = new Button { Text = "Cancel", DialogResult = DialogResult.Cancel, Location = new Point(255, 485), Size = new Size(100, 26) };



			btnOk.Click += (s, e) =>

			{

				if (lvResults.SelectedItems.Count > 0)

				{

					SelectedValue = lvResults.SelectedItems[0].Text;

				}

			};



			this.Controls.Add(btnOk);

			this.Controls.Add(btnCancel);

		}



		public void AddSampleData(string[][] rows)

		{

			allItems.AddRange(rows);

			FilterList();

		}



		private void FilterList()

		{

			lvResults.BeginUpdate();

			lvResults.Items.Clear();

			string query = txtFilter.Text.Trim().ToLowerInvariant();



			int matched = 0;

			foreach (string[] row in allItems)

			{

				if (string.IsNullOrEmpty(query) || (row.Length > 0 && row[0].ToLowerInvariant().Contains(query)))

				{

					ListViewItem item = new ListViewItem(row[0]);

					for (int i = 1; i < row.Length; i++)

					{

						item.SubItems.Add(row[i]);

					}

					lvResults.Items.Add(item);

					matched++;

					if (matched >= 500) break;

				}

			}

			lvResults.EndUpdate();

		}

	}



	// ==========================================

	// DIALOG FILTROWANIA KONTUZJI 1:1 (InjuryFilterDialog.xrc)

	// ==========================================

	public class InjuryFilterDialog : Form

	{

		public InjuryFilterDialog()

		{

			this.Text = "Injury Filter";

			this.Size = new Size(620, 510);

			this.StartPosition = FormStartPosition.CenterParent;

			this.FormBorderStyle = FormBorderStyle.FixedDialog;

			this.MaximizeBox = false;

			this.MinimizeBox = false;

			this.Font = new Font("Segoe UI", 9f);

			this.BackColor = Color.FromArgb(240, 240, 240);



			// 1. Name Box

			GroupBox grpName = new GroupBox { Text = "Name", Location = new Point(12, 10), Size = new Size(280, 55) };

			grpName.Controls.Add(new Label { Text = "Name", Location = new Point(10, 22), AutoSize = true });

			grpName.Controls.Add(new TextBox { Location = new Point(60, 19), Size = new Size(205, 23) });

			this.Controls.Add(grpName);



			// 2. Details Box

			GroupBox grpDetails = new GroupBox { Text = "Details", Location = new Point(12, 70), Size = new Size(280, 345) };

			int dy = 22;

			AddFilterRangeRow(grpDetails, "Minimum Days", 0, 365, ref dy);

			AddFilterRangeRow(grpDetails, "Extra Days", 0, 365, ref dy);

			AddFilterRangeRow(grpDetails, "Inactive Ratio", 0, 100, ref dy);

			AddFilterRangeRow(grpDetails, "Match Injury Percentage", 0, 100, ref dy);

			AddFilterRangeRow(grpDetails, "Goalkeeper Percentage", 0, 100, ref dy);

			AddFilterRangeRow(grpDetails, "Central Defender Percentage", 0, 100, ref dy);



			grpDetails.Controls.Add(new Label { Text = "Is Recurring", Location = new Point(10, dy + 2), AutoSize = true });

			grpDetails.Controls.Add(new CheckBox { Location = new Point(245, dy), Size = new Size(20, 20) });

			dy += 26;



			grpDetails.Controls.Add(new Label { Text = "Is Contagious", Location = new Point(10, dy + 2), AutoSize = true });

			grpDetails.Controls.Add(new CheckBox { Location = new Point(245, dy), Size = new Size(20, 20) });

			this.Controls.Add(grpDetails);



			// 3. Category Box

			GroupBox grpCategory = new GroupBox { Text = "Category", Location = new Point(305, 10), Size = new Size(285, 200) };

			int cy = 22;

			AddFilterComboRow(grpCategory, "Category", new string[] { "Any", "Upper Body", "Lower Body", "Illness" }, ref cy);

			AddFilterComboRow(grpCategory, "Cause", new string[] { "Any", "Match", "Training", "Accident" }, ref cy);

			AddFilterComboRow(grpCategory, "Seriousness", new string[] { "Any", "Minor", "Moderate", "Major", "Severe" }, ref cy);

			AddFilterComboRow(grpCategory, "Age Rule", new string[] { "Any", "Young", "Normal", "Veteran" }, ref cy);

			AddFilterComboRow(grpCategory, "Common Season", new string[] { "Any", "Pre-Season", "Mid-Season", "End-Season" }, ref cy);

			this.Controls.Add(grpCategory);



			// 4. Treatment Box

			GroupBox grpTreat = new GroupBox { Text = "Treatment", Location = new Point(305, 215), Size = new Size(285, 200) };

			int ty = 22;

			AddFilterCheckRow(grpTreat, "Treated By Physio", ref ty);

			AddFilterCheckRow(grpTreat, "Treated By Specialist", ref ty);

			AddFilterCheckRow(grpTreat, "Treated With Injection", ref ty);

			AddFilterCheckRow(grpTreat, "Treated With Isolation", ref ty);

			this.Controls.Add(grpTreat);



			// Buttons OK, Reset, Cancel

			Button btnOk = new Button { Text = "OK", DialogResult = DialogResult.OK, Location = new Point(340, 425), Size = new Size(75, 26) };

			Button btnReset = new Button { Text = "Reset", Location = new Point(425, 425), Size = new Size(75, 26) };

			Button btnCancel = new Button { Text = "Cancel", DialogResult = DialogResult.Cancel, Location = new Point(510, 425), Size = new Size(75, 26) };



			this.Controls.Add(btnOk);

			this.Controls.Add(btnReset);

			this.Controls.Add(btnCancel);

		}



		private void AddFilterRangeRow(GroupBox grp, string label, int min, int max, ref int y)

		{

			grp.Controls.Add(new Label { Text = label, Location = new Point(10, y + 2), Size = new Size(130, 18), AutoSize = false });

			grp.Controls.Add(new NumericUpDown { Location = new Point(145, y), Size = new Size(45, 23), Minimum = min, Maximum = max, Value = min });

			grp.Controls.Add(new Label { Text = "-", Location = new Point(195, y + 2), AutoSize = true });

			grp.Controls.Add(new NumericUpDown { Location = new Point(215, y), Size = new Size(45, 23), Minimum = min, Maximum = max, Value = max });

			y += 28;

		}



		private void AddFilterComboRow(GroupBox grp, string label, string[] items, ref int y)

		{

			grp.Controls.Add(new Label { Text = label, Location = new Point(10, y + 2), Size = new Size(100, 18), AutoSize = false });

			ComboBox cb = new ComboBox { Location = new Point(115, y), Size = new Size(155, 23), DropDownStyle = ComboBoxStyle.DropDownList };

			cb.Items.AddRange(items);

			cb.SelectedIndex = 0;

			grp.Controls.Add(cb);

			y += 28;

		}



		private void AddFilterCheckRow(GroupBox grp, string label, ref int y)

		{

			grp.Controls.Add(new Label { Text = label, Location = new Point(10, y + 2), Size = new Size(160, 18), AutoSize = false });

			grp.Controls.Add(new CheckBox { Location = new Point(245, y), Size = new Size(20, 20) });

			y += 28;

		}

	}

}