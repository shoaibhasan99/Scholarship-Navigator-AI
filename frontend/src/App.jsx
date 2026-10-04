import { useState } from "react";

import {

  Upload,

  GraduationCap,

  Search,

  Brain,

  ShieldCheck,

  ClipboardList,

  CheckCircle,

  AlertTriangle,

  XCircle,

  Loader2,

} from "lucide-react";

import "./App.css";

function App() {

  const [cv, setCv] = useState(null);

  const [transcript, setTranscript] = useState(null);

  const [ielts, setIelts] = useState(null);

  const [country, setCountry] = useState("South Korea");

  const [degreeLevel, setDegreeLevel] = useState("Masters");

  const [loading, setLoading] = useState(false);

  const [result, setResult] = useState(null);

  const [error, setError] = useState(null);

  // ======================================================

  // Submit to FastAPI

  // ======================================================

  const handleSubmit = async (e) => {

    e.preventDefault();

    if (!cv || !transcript) {

      setError(

        "Please upload both CV and transcript."

      );

      return;

    }

    setLoading(true);

    setError(null);

    setResult(null);

    const formData = new FormData();

    formData.append("cv", cv);

    formData.append(

      "transcript",

      transcript

    );

    // IELTS report is optional.

    if (ielts) {

      formData.append(

        "ielts",

        ielts

      );

    }

    formData.append(

      "country",

      country

    );

    formData.append(

      "degree_level",

      degreeLevel

    );

    try {

      const response = await fetch(

        "http://127.0.0.1:8000/analyze",

        {

          method: "POST",

          body: formData,

        }

      );

      const data = await response.json();

      if (!response.ok) {

        throw new Error(

          data.detail ||

          "Analysis failed."

        );

      }

      setResult(data);

    } catch (err) {

      setError(err.message);

    } finally {

      setLoading(false);

    }

  };

  // ======================================================

  // Status Badge

  // ======================================================

  const StatusBadge = ({ status }) => {

    if (status === "eligible") {

      return (

        <span className="badge eligible">

          <CheckCircle size={15} />

          Eligible

        </span>

      );

    }

    if (

      status ===

      "verification_required"

    ) {

      return null;

    }

    if (status === "not_eligible") {

      return (

        <span className="badge rejected">

          <XCircle size={15} />

          Not Eligible

        </span>

      );

    }

    return (

      <span className="badge">

        {status}

      </span>

    );

  };

  // Scholarship matches shown in the UI.

  // Show all discovered scholarships and merge planner/eligibility details.

  const scholarshipMatches = (

    result?.scholarships?.length > 0

      ? result.scholarships

      : result?.shortlist || []

  ).map((scholarship) => {

    const plan = result?.application_plans?.find(

      (item) => item.scholarship_name === scholarship.scholarship_name

    );

    const eligibility = result?.eligibility_results?.find(

      (item) => item.scholarship_name === scholarship.scholarship_name

    );

    return {

      ...scholarship,

      status:

        plan?.status ||

        eligibility?.overall_status ||

        "verification_required",

      deadline:

        plan?.deadline ||

        scholarship.deadline ||

        null,

      notes:

        plan?.notes ||

        (

          eligibility?.overall_status === "not_eligible"

            ? "This opportunity was found, but the current profile does not satisfy at least one requirement."

            : "Potential match. Review the official source and verify any uncertain requirements."

        ),

      missing_documents: plan?.missing_documents || []

    };

  });

  const formatIELTS = (scholarship) => {

    const required = scholarship?.requirements?.ielts_required;

    const minimum = scholarship?.requirements?.minimum_ielts;

    if (required === false) {

      return "Not required / waiver stated";

    }

    if (required === true && minimum != null) {

      return `Required — minimum ${minimum} band`;

    }

    if (required === true) {

      return "Required — minimum band not stated";

    }

    if (minimum != null) {

      return `Minimum ${minimum} band`;

    }

    return "Not stated";

  };

  const formatCGPA = (scholarship) => {

    const cgpa = scholarship?.requirements?.minimum_cgpa;

    const scale = scholarship?.requirements?.cgpa_scale;

    if (cgpa == null) {

      return "Not stated";

    }

    return scale != null

      ? `${cgpa} / ${scale}`

      : `${cgpa}`;

  };

  const formatDegree = (scholarship) => {

    return scholarship?.requirements?.required_degree || "Not stated";

  };

  const hasPreviousCycleData = (scholarship) => {
    return Boolean(
      scholarship?.previous_opening_date ||
      scholarship?.previous_deadline
    );
  };

  return (

    <div className="app">

      {/* ================================================= */}

      {/* HERO */}

      {/* ================================================= */}

      <header className="hero">

        <div className="logo">

          <GraduationCap size={42} />

          <div>

            <h1>

              Scholarship Navigator AI

            </h1>

            <p>

              Scholarship Dhundo,

              Future Banao 🎓

            </p>

          </div>

        </div>

        <p className="hero-description">

          Multi-Agent AI system that

          discovers scholarships,

          checks eligibility,

          verifies requirements and

          prepares your application roadmap.

        </p>

      </header>

      <main className="container">

        {/* ================================================= */}

        {/* UPLOAD */}

        {/* ================================================= */}

        <section className="panel">

          <h2>

            <Upload size={22} />

            Student Documents

          </h2>

          <form

            onSubmit={handleSubmit}

          >

            <div className="upload-grid">

              <label className="upload-box">

                <strong>

                  CV / Resume

                </strong>

                <span>

                  {cv

                    ? cv.name

                    : "Upload PDF"}

                </span>

                <input

                  type="file"

                  accept=".pdf"

                  onChange={(e) =>

                    setCv(

                      e.target.files[0]

                    )

                  }

                />

              </label>

              <label className="upload-box">

                <strong>

                  Academic Transcript

                </strong>

                <span>

                  {transcript

                    ? transcript.name

                    : "Upload PDF"}

                </span>

                <input

                  type="file"

                  accept=".pdf"

                  onChange={(e) =>

                    setTranscript(

                      e.target.files[0]

                    )

                  }

                />

              </label>

              <label className="upload-box">

                <strong>

                  IELTS Report

                  <span style={{ fontWeight: 400 }}> (Optional)</span>

                </strong>

                <span>

                  {ielts

                    ? ielts.name

                    : "Upload PDF"}

                </span>

                <input

                  type="file"

                  accept=".pdf"

                  onChange={(e) =>

                    setIelts(

                      e.target.files[0]

                    )

                  }

                />

              </label>

            </div>

            <div className="filters">

              <div>

                <label>

                  Country

                </label>

                <select

                  value={country}

                  onChange={(e) =>

                    setCountry(e.target.value)

                  }

                >

                  <option value="South Korea">South Korea</option>

                  <option value="China">China</option>

                  <option value="Japan">Japan</option>

                  <option value="Taiwan">Taiwan</option>

                  <option value="Germany">Germany</option>

                  <option value="Malaysia">Malaysia</option>

                  <option value="Singapore">Singapore</option>

                  <option value="Hong Kong">Hong Kong</option>

                </select>

              </div>

              <div>

                <label>

                  Degree Level

                </label>

                <select

                  value={degreeLevel}

                  onChange={(e) =>

                    setDegreeLevel(

                      e.target.value

                    )

                  }

                >

                  <option>

                    Masters

                  </option>

                  <option>

                    PhD

                  </option>

                </select>

              </div>

            </div>

            <button

              className="analyze-button"

              disabled={loading}

            >

              {loading ? (

                <>

                  <Loader2

                    className="spinner"

                    size={20}

                  />

                  Agents Working...

                </>

              ) : (

                <>

                  <Brain size={20} />

                  Start AI Analysis

                </>

              )}

            </button>

          </form>

          {error && (

            <div className="error-box">

              <AlertTriangle

                size={18}

              />

              {error}

            </div>

          )}

        </section>

        {/* ================================================= */}

        {/* AGENT PIPELINE */}

        {/* ================================================= */}

        {result && (

          <>

            <section className="panel">

              <h2>

                <Brain size={22} />

                Agentic AI Workflow

              </h2>

              <div className="agents">

                <Agent

                  icon={<Brain />}

                  name="Profile Agent"

                  description="Extracted student profile"

                />

                <Agent

                  icon={<Search />}

                  name="Discovery Agent"

                  description="Found opportunities"

                />

                <Agent

                  icon={<ShieldCheck />}

                  name="Eligibility Agent"

                  description="Checked requirements"

                />

                <Agent

                  icon={<Search />}

                  name="Evidence Agent"

                  description="Verified uncertain criteria"

                />

                <Agent

                  icon={<ClipboardList />}

                  name="Planner Agent"

                  description="Generated roadmap"

                />

              </div>

            </section>

            {/* ================================================= */}

            {/* PROFILE */}

            {/* ================================================= */}

            <section className="panel">

              <h2>

                👤 Student Profile

              </h2>

              <div className="profile-grid">

                <ProfileItem

                  label="Name"

                  value={

                    result.student_profile?.name

                  }

                />

                <ProfileItem

                  label="Degree"

                  value={

                    result.student_profile

                      ?.academic?.degree

                  }

                />

                <ProfileItem

                  label="University"

                  value={

                    result.student_profile

                      ?.academic?.university

                  }

                />

                <ProfileItem

                  label="CGPA"

                  value={

                    `${result.student_profile

                      ?.academic?.cgpa} / ${result.student_profile

                      ?.academic?.cgpa_scale}`

                  }

                />

                <ProfileItem

                  label="IELTS"

                  value={

                    result.student_profile

                      ?.ielts?.overall ??

                    "Not provided"

                  }

                />

                <ProfileItem

                  label="IELTS Report"

                  value={

                    result.student_profile

                      ?.documents

                      ?.ielts_certificate_uploaded

                      ? "Uploaded"

                      : "Not uploaded"

                  }

                />

                <ProfileItem

                  label="Graduation"

                  value={

                    result.student_profile

                      ?.academic

                      ?.graduation_year

                  }

                />

              </div>

            </section>

            {/* ================================================= */}

            {/* SHORTLIST */}

            {/* ================================================= */}

            <section className="panel">

              <h2>

                🎓 Scholarship Matches

              </h2>

              <div className="scholarship-grid">

                {scholarshipMatches.map(

                  (

                    scholarship,

                    index

                  ) => (

                    <div

                      className="scholarship-card"

                      key={index}

                    >

                      <div className="card-top">

                        <h3>

                          {

                            scholarship

                              .scholarship_name

                          }

                        </h3>

                        <StatusBadge

                          status={

                            scholarship.status

                          }

                        />

                      </div>

                      <div className="scholarship-details">

                        <p>

                          <strong>Opening Date:</strong>{" "}

                          {scholarship.opening_date || "Not stated"}

                        </p>

                        <p>

                          <strong>Deadline:</strong>{" "}

                          {scholarship.deadline || "Not stated"}

                        </p>

                        <p>

                          <strong>IELTS:</strong>{" "}

                          {formatIELTS(scholarship)}

                        </p>

                        {scholarship?.requirements?.minimum_toefl != null && (

                          <p>

                            <strong>TOEFL:</strong>{" "}

                            Minimum {scholarship.requirements.minimum_toefl}

                          </p>

                        )}

                        <p>

                          <strong>Minimum CGPA:</strong>{" "}

                          {formatCGPA(scholarship)}

                        </p>

                        <p>

                          <strong>Degree Required:</strong>{" "}

                          {formatDegree(scholarship)}

                        </p>

                        <p>

                          <strong>Funding:</strong>{" "}

                          {scholarship.funding_details || "Not stated"}

                        </p>

                      </div>

                      {hasPreviousCycleData(scholarship) && (
                        <div
                          className="previous-cycle-reference"
                          style={{
                            marginTop: "14px",
                            padding: "12px 14px",
                            borderRadius: "10px",
                            background: "rgba(255, 193, 7, 0.08)",
                            border: "1px solid rgba(255, 193, 7, 0.28)",
                          }}
                        >
                          <h4 style={{ margin: "0 0 8px 0" }}>
                            📅 Previous Cycle Reference
                            {scholarship.previous_cycle_year
                              ? ` (${scholarship.previous_cycle_year})`
                              : ""}
                          </h4>

                          <p>
                            <strong>Last Cycle Opening Date:</strong>{" "}
                            {scholarship.previous_opening_date || "Not stated"}
                          </p>

                          <p>
                            <strong>Last Cycle Deadline:</strong>{" "}
                            {scholarship.previous_deadline || "Not stated"}
                          </p>

                          <p
                            style={{
                              fontSize: "0.88rem",
                              opacity: 0.78,
                              marginBottom:
                                scholarship.previous_cycle_source_url
                                  ? "8px"
                                  : "0",
                            }}
                          >
                            Previous-cycle dates are for reference only and may
                            change for the upcoming application cycle.
                          </p>

                          {scholarship.previous_cycle_source_url && (
                            <a
                              href={scholarship.previous_cycle_source_url}
                              target="_blank"
                              rel="noreferrer"
                            >
                              View Previous Cycle Source ↗
                            </a>
                          )}
                        </div>
                      )}

                      {scholarship.official_url && (

                        <a

                          href={scholarship.official_url}

                          target="_blank"

                          rel="noreferrer"

                        >

                          View Official Scholarship Source ↗

                        </a>

                      )}

                      <h4>

                        Missing Documents

                      </h4>

                      {scholarship

                        .missing_documents

                        ?.length > 0 ? (

                        scholarship

                          .missing_documents

                          .map(

                            (

                              document,

                              docIndex

                            ) => (

                              <div

                                className="missing-document"

                                key={docIndex}

                              >

                                ⚠️ {document}

                              </div>

                            )

                          )

                      ) : (

                        <div className="good">

                          ✅ No missing documents

                        </div>

                      )}

                    </div>

                  )

                )}

              </div>

            </section>

</>

        )}

      </main>

    </div>

  );

}

function Agent({

  icon,

  name,

  description

}) {

  return (

    <div className="agent-card">

      <div className="agent-icon">

        {icon}

      </div>

      <strong>

        {name}

      </strong>

      <span>

        {description}

      </span>

      <div className="agent-success">

        ✓ Completed

      </div>

    </div>

  );

}

function ProfileItem({

  label,

  value

}) {

  return (

    <div className="profile-item">

      <span>

        {label}

      </span>

      <strong>

        {value || "N/A"}

      </strong>

    </div>

  );

}

export default App;
