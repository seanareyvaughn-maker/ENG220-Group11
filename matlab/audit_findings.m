%eins = readtable("additional_eins.csv");
%ueis = readtable("additional_ueis.csv");
%plans = readtable("corrective_action_plans.csv");
if ~exist("awards", "var")
    awards = readtable("federal_awards.csv");
end
%findingsText = readtable("findings_text.csv");
if ~exist("findings", "var")
    findings = readtable("findings.csv");
end

if ~exist("general", "var")
    general = readtable("general.csv");
end
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
programs = strtrim(string(AwardsCubaFindings.federal_program_name));
programs(ismissing(programs) | programs == "") = "<missing>";

mwPrograms = strtrim(string(AwardsCubaMaterialWeakness.federal_program_name));
mwPrograms(ismissing(mwPrograms) | mwPrograms == "") = "<missing>";

[grpAll, programNames] = findgroups(programs);
programCounts = splitapply(@numel, programs, grpAll);

[grpMW, mwNames] = findgroups(mwPrograms);
mwCountsByProgram = splitapply(@numel, mwPrograms, grpMW);

mwCounts = zeros(size(programNames));
[tf, loc] = ismember(programNames, mwNames);
mwCounts(tf) = mwCountsByProgram(loc(tf));

nonMWCounts = programCounts - mwCounts;

[programCounts, order] = sort(programCounts, "descend");
programNames = programNames(order);
mwCounts = mwCounts(order);
nonMWCounts = nonMWCounts(order);

programCounts = flipud(programCounts);
programNames = flipud(programNames);
mwCounts = flipud(mwCounts);
nonMWCounts = flipud(nonMWCounts);

x = categorical(programNames);
x = reordercats(x, programNames);

figure(10)
clf

h = barh(x, [mwCounts nonMWCounts], "stacked", "EdgeColor", "none");
ax = gca;
ax.TickLabelInterpreter = "none";
h(1).FaceColor = [0.85 0.2 0.2];
h(2).FaceColor = [0.75 0.75 0.75];

xlabel("Number of Cuba findings")
ylabel("Affected Federal program")
title("Audit Findings in Cuba")
legend(h, {"Material weakness", "Non-material weakness"}, "Location", "best")
grid on

% ---- Expenditure chart ----
expendedVar = "amount_expended";   

programs = strtrim(string(AwardsCubaFindings.federal_program_name));
programs(ismissing(programs) | programs == "") = "<missing>";

mwPrograms = strtrim(string(AwardsCubaMaterialWeakness.federal_program_name));
mwPrograms(ismissing(mwPrograms) | mwPrograms == "") = "<missing>";

expended = double(AwardsCubaFindings.(expendedVar));
mwExpendedData = double(AwardsCubaMaterialWeakness.(expendedVar));

[grpAll, programNames] = findgroups(programs);
totalExpended = splitapply(@(x) sum(x, "omitnan"), expended, grpAll);

[grpMW, mwNames] = findgroups(mwPrograms);
mwExpendedByProgram = splitapply(@(x) sum(x, "omitnan"), mwExpendedData, grpMW);

mwExpended = zeros(size(programNames));
[tf, loc] = ismember(programNames, mwNames);
mwExpended(tf) = mwExpendedByProgram(loc(tf));

nonMWExpended = totalExpended - mwExpended;

[totalExpended, order] = sort(totalExpended, "descend");
programNames = programNames(order);
mwExpended = mwExpended(order);
nonMWExpended = nonMWExpended(order);

totalExpended = flipud(totalExpended);
programNames = flipud(programNames);
mwExpended = flipud(mwExpended);
nonMWExpended = flipud(nonMWExpended);

x = categorical(programNames);
x = reordercats(x, programNames);

figure(20)
clf

h = barh(x, [mwExpended nonMWExpended], "stacked", "EdgeColor", "none");
ax = gca;
ax.TickLabelInterpreter = "none";
h(1).FaceColor = [0.85 0.2 0.2];
h(2).FaceColor = [0.75 0.75 0.75];

xlabel("Total expended amount")
ylabel("Affected Federal program")
title("Cuba Findings by Expended Amount")
legend(h, {"Material weakness", "Non-material weakness"}, "Location", "best")
grid on

% ---- Findings count by time window ----
currentYear = max([NMFindings.audit_year; CubaFindings.audit_year], [], "omitnan");

periods = [1 5 10];
periodLabels = ["Past 1 year", "Past 5 years", "Past 10 years"];

nmCounts = zeros(size(periods));
cubaCounts = zeros(size(periods));

for k = 1:numel(periods)
    yearStart = currentYear - periods(k) + 1;

    nmCounts(k) = sum(NMFindings.audit_year >= yearStart & NMFindings.audit_year <= currentYear);
    cubaCounts(k) = sum(CubaFindings.audit_year >= yearStart & CubaFindings.audit_year <= currentYear);
end

figure(30)
clf

x = categorical(periodLabels, periodLabels);
h = bar(x, [nmCounts(:) cubaCounts(:)], "grouped");

h(1).FaceColor = [0.2 0.5 0.85];
h(2).FaceColor = [0.85 0.2 0.2];

set(gca, "YScale", "log")

xlabel("Time window")
ylabel("Number of findings (log scale)")
title("Findings in New Mexico vs Cuba")
legend(h, {"New Mexico", "Cuba"}, "Location", "best")
grid on

%todo:
%1 year, 5 years, 10 years


%state, county,