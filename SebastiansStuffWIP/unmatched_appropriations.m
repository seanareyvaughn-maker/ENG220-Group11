%datatable = readtable("nm-capital-appropriations-2026-10-13.csv");

CSV = "nm-capital-appropriations-2026-10-13.csv";

opts = detectImportOptions(CSV);
opts = setvartype(opts, "LegislativeSponsors", "string");   % replace with the exact column name
datatable = readtable(CSV, opts);

%appropriated, expended, and remaining balance columns
appIdx = 15;
expIdx = 18;
balIdx = 21;
dateIdx = 12;
cityIdx = 7;
countyIdx = 8; 

%reathorized funds
reauthIdx = 16;
reauthAmount = datatable{:, reauthIdx};

appropriated = datatable{:, appIdx};
expended = datatable{:, expIdx};
remaining = datatable{:, balIdx};

expected = expended + remaining;

validMask = ~isnan(appropriated) & ~isnan(expended) & ~isnan(remaining);

%appropriated amount does not match expended + remaining amount
%should be empty because it should be automatically calculated by the
%system
mismatchMask = validMask & abs(appropriated - expected) > 0.01;

mismatchRows = datatable(mismatchMask, :);
mismatchRows.AmountDifference = appropriated(mismatchMask) - expected(mismatchMask);

%rows where appropriate, expended, or remaining amounts are NaN values
missingRows = datatable(~validMask, :);

% rows with negative values
negativeBalanceMask = appropriated < 0 | expended < 0 | remaining < 0;
reauthGreaterMask = reauthAmount >= expended;
negativeMask = negativeBalanceMask & ~reauthGreaterMask;
negativeRows = datatable(negativeMask, :);

%rows with no appropriated amounts but expended or remaining is > 0
reauthorizedMask = datatable{:, reauthIdx} > 0;
activeMask = expended > 0 | remaining > 0;
zeroMask = appropriated == 0 & activeMask & ~reauthorizedMask;
zeroRows = datatable(zeroMask, :);

allSuspiciousRows = datatable(mismatchMask | negativeMask | zeroMask, :);

negativeRowNums = find(negativeMask);
zeroRowNums = find(zeroMask);

idIdx = 1;

maxPoints = 60;

mainFig = figure('Units', 'pixels', ...
    'Position', centerFigurePosition(1100, 750), ...
    'Name', "Unmatched Appropriations", ...
    'NumberTitle', 'off');
tg = uitabgroup(mainFig);

% Negative-value rows
if any(negativeMask)
    negIdx = find(negativeMask);
    negScore = abs(appropriated(negativeMask)) + abs(expended(negativeMask)) + abs(remaining(negativeMask));
    [~, order] = sort(negScore, 'descend');
    negIdx = negIdx(order);
    negIdx = negIdx(1:min(maxPoints, numel(negIdx)));

    negLabels = string(datatable{negIdx, idIdx});
    negVals = [appropriated(negIdx), expended(negIdx), remaining(negIdx)];

    tab = uitab(tg, 'Title', 'Negative Balance Projects');
    ax = axes('Parent', tab);
    b = bar(ax, categorical(negLabels), negVals, 'grouped');
    for k = 1:numel(b)
        b(k).BarWidth = 0.95;
    end

    title(ax, "Negative Balance Projects")
    xlabel(ax, "Appropriation ID")
    ylabel(ax, "Amount")
    legend(ax, "Appropriated", "Expended", "Remaining", 'Location', 'best')
    grid(ax, 'on')
    xtickangle(ax, 45)
    pan(ax, 'on')
end

% Zero-appropriation rows with activity
if any(zeroMask)
    zeroIdx = find(zeroMask);
    zeroScore = expended(zeroMask);
    [~, order] = sort(zeroScore, 'descend');
    zeroIdx = zeroIdx(order);
    zeroIdx = zeroIdx(1:min(maxPoints, numel(zeroIdx)));

    zeroLabels = string(datatable{zeroIdx, idIdx});
    zeroVals = expended(zeroIdx);

    tab = uitab(tg, 'Title', 'Zero Activity');
    ax = axes('Parent', tab);
    barh(ax, categorical(zeroLabels), zeroVals)
    title(ax, "Top Zero-Appropriation Rows with Activity")
    xlabel(ax, "Expended Amount")
    ylabel(ax, "Appropriation ID")
    grid(ax, 'on')
end

% Heatmap with separate state total column
stateTotal = sum(totals, 2, "omitnan");

tab = uitab(tg, 'Title', 'Year by County');
gl = uigridlayout(tab, [1 2]);
gl.ColumnWidth = {'1x', 140};
gl.RowHeight = {'1x'};
gl.Padding = [0 0 0 0];
gl.ColumnSpacing = 10;

% Main county heatmap
p1 = uipanel(gl);
h = heatmap(p1, string(countyList), string(yearList), totals);
h.Title = "Amount Appropriated by Year and County";
h.XLabel = "County";
h.YLabel = "Year";
h.CellLabelColor = "none";
h.Colormap = parula;

% State total heatmap
p2 = uipanel(gl);
h2 = heatmap(p2, "State Total", string(yearList), stateTotal);
h2.Title = "";
h2.XLabel = "";
h2.YLabel = "";
h2.CellLabelColor = "none";
h2.Colormap = parula;
h2.ColorLimits = h.ColorLimits;


% Map with year selector
dateData = datatable{:, dateIdx};
if isdatetime(dateData)
    yr = year(dateData);
elseif isnumeric(dateData)
    yr = dateData;
else
    yr = year(datetime(string(dateData)));
end

countyRaw = strtrim(string(datatable{:, countyIdx}));
countyKey = normalizeCountyKey(countyRaw);

validMapMask = ~isnan(appropriated) & ~isnan(yr) & countyKey ~= "" & ~ismissing(countyKey);

yearList = sort(unique(yr(validMapMask)));
[countyKeyList, ~, countyGroup] = unique(countyKey(validMapMask), "stable");
[~, ~, yearGroup] = unique(yr(validMapMask));

countyTotals = accumarray([yearGroup, countyGroup], appropriated(validMapMask), ...
    [numel(yearList), numel(countyKeyList)], @sum, 0);

shpFiles = dir("*county*.shp");
if isempty(shpFiles)
    shpFiles = dir("*.shp");
end
if isempty(shpFiles)
    error("No shapefile found in the current folder.");
end

GT = readgeotable(shpFiles(1).name);
vars = string(GT.Properties.VariableNames);

countyField = "";
for name = ["NAMELSAD", "NAME", "COUNTYNAME", "County", "CountyName"]
    if any(vars == name)
        countyField = name;
        break
    end
end
if countyField == ""
    error("No county name field found in the shapefile.");
end

stateField = "";
for name = ["STATEFP", "STUSPS", "STATE", "STATE_NAME"]
    if any(vars == name)
        stateField = name;
        break
    end
end
if stateField == ""
    error("No state field found in the shapefile.");
end

stateVals = string(GT.(stateField));
if stateField == "STATEFP"
    nmGT = GT(stateVals == "35", :);
elseif stateField == "STUSPS"
    nmGT = GT(stateVals == "NM", :);
else
    nmGT = GT(contains(upper(stateVals), "NEW MEXICO") | stateVals == "NM", :);
end

nmGT.CountyKey = normalizeCountyKey(nmGT.(countyField));

commonLim = [min(countyTotals(:)) max(countyTotals(:))];
if commonLim(1) == commonLim(2)
    commonLim = commonLim + [-0.5 0.5];
end

tab = uitab(tg, 'Title', 'NM County Map');
uilabel(tab, 'Text', 'Year:', 'Position', [20 610 40 22]);

yearDrop = uidropdown(tab, ...
    'Items', string(yearList), ...
    'Value', string(yearList(end)), ...
    'Position', [70 608 120 24]);


ax = axes('Parent', tab, 'Position', [0.05 0.08 0.90 0.82]);

yearDrop.ValueChangedFcn = @(src, ~) updateCountyMap( ...
    ax, nmGT, countyField, countyKeyList, countyTotals, yearList, src.Value, commonLim);

updateCountyMap(ax, nmGT, countyField, countyKeyList, countyTotals, yearList, yearDrop.Value, commonLim);










%helper functions

function pos = centerFigurePosition(figWidth, figHeight)
screen = get(groot, 'ScreenSize');
figWidth = min(figWidth, floor(screen(3) * 0.80));
figHeight = min(figHeight, floor(screen(4) * 0.80));
left = screen(1) + (screen(3) - figWidth) / 2;
bottom = screen(2) + (screen(4) - figHeight) / 2;
pos = [left, bottom, figWidth, figHeight];
end

function updateCountyMap(ax, nmGT, countyField, countyKeyList, countyTotals, yearList, yearValue, commonLim)
if isstring(yearValue) || ischar(yearValue)
    yearValue = str2double(string(yearValue));
end

yearIdx = find(yearList == yearValue, 1);
if isempty(yearIdx)
    error("Selected year is not available.");
end

countyAmounts = countyTotals(yearIdx, :);
nmAmount = nan(height(nmGT), 1);

[tf, loc] = ismember(nmGT.CountyKey, countyKeyList);
nmAmount(tf) = countyAmounts(loc(tf));

cmap = parula(256);
geom = nmGT.Shape;
countyNames = string(nmGT.(countyField));
countyNames = replace(countyNames, " County", "");
countyNames = replace(countyNames, " county", "");
countyNames = strtrim(countyNames);

cla(ax)
hold(ax, "on")

% First pass: draw all counties
for k = 1:height(nmGT)
    amt = nmAmount(k);

    if isnan(amt)
        faceColor = [0.90 0.90 0.90];
    elseif commonLim(1) == commonLim(2)
        faceColor = cmap(end, :);
    else
        t = (amt - commonLim(1)) / (commonLim(2) - commonLim(1));
        t = max(0, min(1, t));
        faceColor = interp1(linspace(0, 1, size(cmap, 1)), cmap, t, "linear");
    end

    geoshow(ax, nmGT(k, :), ...
        "FaceColor", faceColor, ...
        "EdgeColor", [0.35 0.35 0.35]);
end

% Second pass: draw labels and leader line on top of everything
for k = 1:height(nmGT)
    [latlim, lonlim] = bounds(geom(k));
    lat = mean(latlim, "omitnan");
    lon = mean(lonlim, "omitnan");

    if ~isnan(lat) && ~isnan(lon)
        labelLat = lat;
        labelLon = lon;

        if strcmpi(countyNames(k), "Los Alamos")
    labelLat = lat + 0.18;

    % dark outline
    line(ax, [lon labelLon], [lat labelLat], ...
        "Color", [0.10 0.10 0.10], ...
        "LineWidth", 3);

    % light top line
    line(ax, [lon labelLon], [lat labelLat], ...
        "Color", [1 1 1], ...
        "LineWidth", 1.5);
end


        text(ax, labelLon, labelLat, countyNames(k), ...
            "Color", [0.15 0.15 0.15], ...
            "FontSize", 8, ...
            "FontWeight", "bold", ...
            "HorizontalAlignment", "center", ...
            "VerticalAlignment", "middle", ...
            "Interpreter", "none", ...
            "BackgroundColor", [0.97 0.97 0.97], ...
            "Margin", 1, ...
            "Clipping", "off");
    end
end

axis(ax, "equal")
axis(ax, "off")
title(ax, "New Mexico Appropriations by County, " + string(yearValue))
colormap(ax, cmap)
clim(ax, commonLim)
cb = colorbar(ax);
cb.Label.String = "Total Appropriated";
end



function key = normalizeCountyKey(x)
key = lower(strtrim(string(x)));
key = replace(key, ".", "");
key = replace(key, " county", "");
key = replace(key, " parish", "");
key = replace(key, " borough", "");
end

