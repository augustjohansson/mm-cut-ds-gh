function plotter(a)

    aorg = a;
    a(:,1) = [];

    figL2 = 1;
    figH10 = 2;

    as = a(:, [1, 2, 3]);
    am = a(:, [4, 5, 6]);

    asL2 = a(:, [1, 2]);
    asH10 = a(:, [1, 3]);
    amL2 = a(:, [4, 5]);
    amH10 = a(:, [4, 6]);

    colors = lines(2);
    cs = colors(1,:);
    cm = colors(2,:);

    % L2
    [slopesL2] = convplot(asL2, 2, 'fignos', figL2, 'colors', cs);
    [slopemL2,~,~,figL2] = convplot(amL2, 2, 'fignos', figL2, 'colors', cm);

    % H10
    [slopesH10] = convplot(asH10, 2, 'fignos', figH10, 'colors', cs);
    [slopemH10,~,~,figH10] = convplot(amH10, 2, 'fignos', figH10, 'colors', cm);

    sstrL2 = sprintf('Std L2 %g', slopesL2(2));
    sstrH10 = sprintf('Std H10 %g', slopesH10(2));
    mstrL2 = sprintf('Multimesh L2 %g', slopemL2(2));
    mstrH10 = sprintf('Multimesh H10 %g', slopemH10(2));
    sstr = {sstrL2, sstrH10};
    mstr = {mstrL2, mstrH10};

    % Legend
    figs = {figL2, figH10};

    for ifig = 1:numel(figs)
        fig = figs{ifig};

        ax = findobj(fig, 'Type', 'axes'); assert(numel(ax) == 1);
        ln = findobj(ax, 'Type', 'line'); assert(numel(ln) == 4);

        if norm(ln(1).Color - cs) < eps
            str1 = sstr{ifig};
            str2 = mstr{ifig};
        else
            str1 = mstr{ifig};
            str2 = sstr{ifig};
        end

        legend(ax, [ln(3), ln(1)], {str2, str1}, 'location', 'northwest');

    end

end
