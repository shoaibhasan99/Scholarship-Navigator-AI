from langgraph.graph import (



    StateGraph,



    START,



    END



)







from state import ScholarshipState







from agents.profile_agent import build_profile







from agents.discovery_agent import (



    discover_scholarships



)







from agents.eligibility_agent import (



    evaluate_all_scholarships



)







from agents.scholarship_verifier_agent import (



    verify_scholarship_sources



)







from agents.planner_agent import (



    generate_application_plans,



    get_shortlist



)











# ==================================================



# PROFILE NODE



# ==================================================







def profile_node(



    state: ScholarshipState



) -> ScholarshipState:







    print("\n" + "=" * 60)



    print("🧠 LANGGRAPH → PROFILE AGENT")



    print("=" * 60)







    try:







        profile = build_profile(
            state["cv_path"],
            state["transcript_path"],
            state.get("ielts_path")
        )







        messages = state.get(



            "messages",



            []



        )







        messages.append(



            "Profile Agent completed successfully."



        )







        return {



            **state,



            "student_profile": profile,



            "current_agent": "profile",



            "messages": messages



        }







    except Exception as error:







        return {



            **state,



            "error": str(error),



            "current_agent": "profile"



        }











# ==================================================



# DISCOVERY NODE



# ==================================================







def discovery_node(



    state: ScholarshipState



) -> ScholarshipState:







    print("\n" + "=" * 60)



    print("🔎 LANGGRAPH → DISCOVERY AGENT")



    print("=" * 60)







    profile = state["student_profile"]







    scholarships = discover_scholarships(



        profile=profile,







        country=state.get(



            "country",



            "South Korea"



        ),







        degree_level=state.get(



            "degree_level",



            "Masters"



        )



    )







    messages = state.get(



        "messages",



        []



    )







    messages.append(



        f"Discovery Agent found "



        f"{len(scholarships)} scholarships."



    )







    return {



        **state,



        "scholarships": scholarships,



        "current_agent": "discovery",



        "messages": messages



    }











# ==================================================



# ELIGIBILITY NODE



# ==================================================







def eligibility_node(



    state: ScholarshipState



) -> ScholarshipState:







    print("\n" + "=" * 60)



    print("⚖️ LANGGRAPH → ELIGIBILITY AGENT")



    print("=" * 60)







    results = evaluate_all_scholarships(



        state["student_profile"],



        state["scholarships"]



    )







    messages = state.get(



        "messages",



        []



    )







    messages.append(



        f"Eligibility Agent evaluated "



        f"{len(results)} scholarships."



    )







    return {



        **state,



        "eligibility_results": results,



        "current_agent": "eligibility",



        "messages": messages



    }











# ==================================================



# ROUTER AFTER ELIGIBILITY



# ==================================================







def route_after_eligibility(



    state: ScholarshipState



) -> str:







    results = state[



        "eligibility_results"



    ]







    attempts = state.get(



        "verification_attempts",



        0



    )







    needs_verification = any(



        result.verification_needed



        for result in results



    )







    # ------------------------------------------



    # First time uncertainty is detected



    # ------------------------------------------







    if (



        needs_verification



        and attempts < 1



    ):







        print(



            "\n🔀 LangGraph decision: "



            "Missing or uncertain evidence."



        )







        print(



            "➡️ Routing to Real Evidence Agent..."



        )







        return "evidence"







    # ------------------------------------------



    # Evidence already attempted



    # ------------------------------------------







    if needs_verification:







        print(



            "\n🔀 Evidence already checked."



        )







        print(



            "⚠️ Some requirements remain uncertain."



        )







        print(



            "➡️ Sending flagged results "



            "to Planner Agent..."



        )







        return "planner"







    # ------------------------------------------



    # Everything verified



    # ------------------------------------------







    print(



        "\n🔀 All available eligibility "



        "checks completed."



    )







    print(



        "➡️ Routing directly "



        "to Planner Agent..."



    )







    return "planner"











# ==================================================



# REAL EVIDENCE NODE



# ==================================================







def evidence_node(



    state: ScholarshipState



) -> ScholarshipState:







    print("\n" + "=" * 60)



    print("🔍 LANGGRAPH → REAL EVIDENCE AGENT")



    print("=" * 60)







    verified_scholarships, evidence = (



        verify_scholarship_sources(



            state["scholarships"]



        )



    )







    attempts = (



        state.get(



            "verification_attempts",



            0



        )



        + 1



    )







    messages = state.get(



        "messages",



        []



    )







    messages.append(



        f"Evidence Agent checked "



        f"{len(verified_scholarships)} "



        f"official scholarship sources."



    )







    return {



        **state,







        # IMPORTANT:



        # Replace unverified discovery results



        # with enriched official-source results



        "scholarships":



            verified_scholarships,







        "evidence_records":



            evidence,







        "verification_attempts":



            attempts,







        "current_agent":



            "evidence",







        "messages":



            messages



    }











# ==================================================



# PLANNER NODE



# ==================================================







def planner_node(



    state: ScholarshipState



) -> ScholarshipState:







    print("\n" + "=" * 60)



    print("📋 LANGGRAPH → PLANNER AGENT")



    print("=" * 60)







    plans = generate_application_plans(



        state["student_profile"],



        state["scholarships"],



        state["eligibility_results"]



    )







    shortlist = get_shortlist(

        plans,

        state["eligibility_results"]

    )







    messages = state.get(



        "messages",



        []



    )







    messages.append(



        f"Planner Agent generated "



        f"{len(shortlist)} shortlisted opportunities."



    )







    return {



        **state,







        "application_plans":



            plans,







        "shortlist":



            shortlist,







        "current_agent":



            "planner",







        "messages":



            messages



    }











# ==================================================



# BUILD LANGGRAPH



# ==================================================







workflow = StateGraph(



    ScholarshipState



)











workflow.add_node(



    "profile",



    profile_node



)







workflow.add_node(



    "discovery",



    discovery_node



)







workflow.add_node(



    "eligibility",



    eligibility_node



)







workflow.add_node(



    "evidence",



    evidence_node



)







workflow.add_node(



    "planner",



    planner_node



)











# ==================================================



# EDGES



# ==================================================







workflow.add_edge(



    START,



    "profile"



)







workflow.add_edge(



    "profile",



    "discovery"



)







workflow.add_edge(



    "discovery",



    "eligibility"



)











# ==================================================



# CONDITIONAL ROUTING



# ==================================================







workflow.add_conditional_edges(



    "eligibility",







    route_after_eligibility,







    {



        "evidence": "evidence",



        "planner": "planner"



    }



)











# IMPORTANT:



# Evidence now returns to Eligibility



workflow.add_edge(



    "evidence",



    "eligibility"



)











workflow.add_edge(



    "planner",



    END



)











# ==================================================



# COMPILE GRAPH



# ==================================================







scholarship_graph = (



    workflow.compile()



)











# ==================================================



# TEST COMPLETE AGENTIC SYSTEM



# ==================================================







if __name__ == "__main__":







    initial_state = {







        "cv_path":



            "../uploads/CV.pdf",







        "transcript_path":



            "../uploads/Transcript.pdf",

        # Optional IELTS report.
        # Set this to a PDF path when manually testing an IELTS upload.
        "ielts_path":
            None,







        "country":



            "South Korea",







        "degree_level":



            "Masters",







        # Prevent infinite



        # Evidence ↔ Eligibility loop



        "verification_attempts":



            0,







        "messages":



            []



    }











    print(



        "\n🚀 SCHOLARSHIP NAVIGATOR AI"



    )







    print(



        "Starting Agentic AI workflow...\n"



    )











    final_state = (



        scholarship_graph.invoke(



            initial_state



        )



    )











    print(



        "\n"



        + "=" * 60



    )







    print(



        "🎓 FINAL SHORTLIST"



    )







    print(



        "=" * 60



    )











    shortlist = final_state.get(



        "shortlist",



        []



    )











    if not shortlist:



        print(

            "No scholarships currently have enough "

            "positive verified evidence for the shortlist."

        )



        plans = final_state.get(

            "application_plans",

            []

        )



        if plans:

            print(

                f"{len(plans)} opportunities were still analyzed "

                "and remain available for manual review."

            )











    for index, plan in enumerate(



        shortlist,



        start=1



    ):







        print(



            f"\n{index}. "



            f"{plan.scholarship_name}"



        )







        print(



            f"   Status: "



            f"{plan.status}"



        )







        print(



            f"   Deadline: "



            f"{plan.deadline}"



        )







        if plan.missing_documents:







            print(



                "   Missing Documents:"



            )







            for document in (



                plan.missing_documents



            ):







                print(



                    f"      ⚠️ {document}"



                )











    print(



        "\n"



        + "=" * 60



    )







    print(



        "🤖 AGENT ACTIVITY LOG"



    )







    print(



        "=" * 60



    )











    for message in final_state.get(



        "messages",



        []



    ):







        print(



            f"✅ {message}"



        )