%eins = readtable("additional_eins.csv");
%ueis = readtable("additional_ueis.csv");
%plans = readtable("corrective_action_plans.csv");
awards = readtable("federal_awards.csv");
%findingsText = readtable("findings_text.csv");
findings = readtable("findings.csv");
general = readtable("general.csv");
%sefa = readtable("notes_to_sefa.csv");
%passthrough = readtable("passthrough.csv");

NM = general(general.auditee_state == "NM", :);
Cuba = NM(NM.auditee_city == "CUBA", :);

%data on all of NM
NMReportIDs = NM{:,1};
NMFindings = findings(ismember(findings.report_id, NMReportIDs), :);
NMMaterialWeakness = NMFindings(NMFindings.is_material_weakness == "Y", :);

AwardsNMFindings = awards(ismember(awards.report_id, NMFindings.report_id), :);
AwardsNMMaterialWeakness = awards(ismember(awards.report_id, NMMaterialWeakness.report_id), :);

programsNMFindings = unique(string(AwardsNMFindings.federal_program_name));
programsNMMaterialWeakness = unique(string(AwardsNMMaterialWeakness.federal_program_name));

%Same data but only for Cuba
CubaReportIDs = Cuba{:,1};
CubaFindings = findings(ismember(findings.report_id, CubaReportIDs), :);
CubaMaterialWeakness = CubaFindings(CubaFindings.is_material_weakness == "Y", :);

AwardsCubaFindings = awards(ismember(awards.report_id, CubaFindings.report_id), :);
AwardsCubaMaterialWeakness = awards(ismember(awards.report_id, CubaMaterialWeakness.report_id), :);

programsCubaFindings = unique(string(AwardsCubaFindings.federal_program_name));
programsCubaMaterialWeakness = unique(string(AwardsCubaMaterialWeakness.federal_program_name));

%Programs affected
programs = string(AwardsCubaFindings.federal_program_name);
mwPrograms = unique(string(AwardsCubaMaterialWeakness.federal_program_name));

programs = strtrim(programs);
programs(ismissing(programs) | programs == "") = "<missing>";

[grp, programNames] = findgroups(programs);
programCounts = splitapply(@numel, programs, grp);

isMW = ismember(programNames, mwPrograms);

[programCounts, order] = sort(programCounts, "descend");
programNames = programNames(order);
isMW = isMW(order);

programCounts = flipud(programCounts);
programNames = flipud(programNames);
isMW = flipud(isMW);

x = categorical(programNames);
x = reordercats(x, programNames);

figure
h1 = barh(x, programCounts, "FaceColor", [0.75 0.75 0.75], "EdgeColor", "none");
hold on
h2 = barh(x(isMW), programCounts(isMW), "FaceColor", [0.85 0.2 0.2], "EdgeColor", "none");
hold off

xlabel("Number of Cuba findings")
ylabel("Affected Federal program")
title("Audit Findings in Cuba")
legend([h1 h2], {"All programs", "Material weakness"}, "Location", "best")
grid on

% ---- Expenditure chart ----
expendedVar = "amount_expended";   % change this if your column name differs

expended = double(AwardsCubaFindings.(expendedVar));

[grp, programNames] = findgroups(programs);
programExpended = splitapply(@(x) sum(x, "omitnan"), expended, grp);

isMW = ismember(programNames, mwPrograms);

[programExpended, order] = sort(programExpended, "descend");
programNames = programNames(order);
isMW = isMW(order);

programExpended = flipud(programExpended);
programNames = flipud(programNames);
isMW = flipud(isMW);

x = categorical(programNames);
x = reordercats(x, programNames);

figure
h1 = barh(x, programExpended, "FaceColor", [0.75 0.75 0.75], "EdgeColor", "none");
hold on
h2 = barh(x(isMW), programExpended(isMW), "FaceColor", [0.85 0.2 0.2], "EdgeColor", "none");
hold off

xlabel("Total expended amount")
ylabel("Affected Federal program")
title("Cuba Findings by Expended Amount")
legend([h1 h2], {"All programs", "Material weakness"}, "Location", "best")
grid on