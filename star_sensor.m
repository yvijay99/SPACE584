phi = -0.8 + rand*0.2;
FOV = pi/8;
nres = 256;
nangle = 5;
nstars = 100;
spacing_fact = 10;
use_photo = true;
star_table_path = 'star_table2.csv';
starfield_path = 'star_field2.png';
nwpx=4608; % Number of pixels wide of starfield
nhpx=2592; % Number of pixels tall of starfield
x0 = 3270;
y0 = 1608; % Image reads upside down 
wFOV=102;
hFOV=67;

% Reprocess files
% Read the star table from the CSV file
star_table = import_star_table('star_table2.csv', x0, y0, nwpx, nhpx, wFOV, hFOV);
save('star_table.mat', 'star_table');

% Import actual starfield image and save as .mat file
img = imread('star_field2.png');
save('star_field.mat', 'img');

% Generate synthetic data. First, create a random starfield, then create
% the lookup table of the distances to the closest stars from each star,
% then create a synthetic photo of the starfield at boresight angle phi
if ~use_photo
    star_table = generate_star_table(nstars,FOV,nres,spacing_fact);
    star_lookup = generate_star_lookup_table(star_table,nangle);
    st_im = generate_st_im(star_table, phi, FOV, nres, 2, 255);

% Import actual starfield image
else
    struct = load("star_table.mat");
    star_table = struct.star_table;
    star_lookup = generate_star_lookup_table(star_table,nangle);
    [st_im,nres] = crop_starfield('star_field.mat',phi,FOV,x0,y0,nwpx,nhpx,wFOV,hFOV);
end

% Analyze image. First, create list the relative coords of the stars in the
% image, then attempt to match a star to a known one using the lookup table
star_ls = identify_stars(st_im,FOV);

if size(star_ls)<3
    fprintf('Only %.0f stars in view, likely to fail.\n',size(star_ls))
end

star_pos_error = 10*wFOV/nwpx*pi/180;
[star_num,deltaphi,deltatheta] = match_to_lookup(star_ls,star_pos_error,star_lookup);

% Finally, compute boresight phi
boresight_phi = compute_boresight_phi(star_num,star_table,deltaphi);
fprintf('####\nEstimated attitude: %.3f\nTrue attitude: %.3f.\n####\n',boresight_phi,phi)

% Plotting for debug
show_table = true;

% Reset/clear the plot
clf; % Clear current figure

if show_table && ~use_photo
    % Create a subplot for the scatter plot
    subplot(1, 2, 1);
    % Set figure size to make it wider and less tall
    figure_width = 2400; % Width of the figure in pixels
    figure_height = 600; % Height of the figure in pixels
    set(gcf, 'Position', [100, 100, figure_width, figure_height]); % Set figure position and size

    hold on; % Retain current plot when adding new plots
    plot([phi-FOV/2, phi+FOV/2, phi+FOV/2, phi-FOV/2, phi-FOV/2], [-FOV/2, -FOV/2, FOV/2, FOV/2, -FOV/2], 'red');
    scatter(star_table(:, 1), star_table(:, 2), star_table(:, 3).^4 * 10, 'white');
    % Show the identified star
    if star_num ~= -1
        scatter(star_table(star_num,1), star_table(star_num,2), 200, 'green', 'Marker', 'o', 'LineWidth', 2);
    end
    hold off; % Release the plot hold

    % Set axes background color to black
    ax = gca; % Get current axes
    ax.Color = [0 0 0]; % Black background
    xlabel('Azimuth (\phi)');
    ylabel('Inclination (\theta)');
    xlim([-3*pi/8, 7/8*pi]); % Set x-axis limits from -pi to pi
    
    % Set x-axis ticks as fractions of pi
    xticks([-pi/4, 0, pi/4, pi/2, 3/4*pi]);
    xticklabels({'-\pi/4', '0', '\pi/4', '\pi/2', '3\pi/4'});
    axis equal; % Set equal scaling for both axes
    title('Full starfield');

    % Create a subplot for the image
    subplot(1, 2, 2);
    hold on; 
    imshow(st_im, [], 'XData', linspace(-FOV/2,FOV/2,nres), 'YData', linspace(-FOV/2,FOV/2,nres));
    scatter(star_ls(:, 1), star_ls(:, 2), 500, 'red', 'MarkerEdgeColor', 'red', 'MarkerFaceColor', 'none');
    scatter(deltaphi, deltatheta, 300, 'green', 'MarkerEdgeColor', 'green', 'MarkerFaceColor', 'none');
    hold off; 
    xlabel('\delta\phi');
    ylabel('\delta\theta');
    axis on;
    title('Synthetic Star Tracker Image');

elseif use_photo

    phi_ax = (-x0:nwpx-x0)*wFOV/nwpx*pi/180;
    theta_ax = (-y0:nhpx-y0)*hFOV/nhpx*pi/180;

    % Create a new figure for displaying the images
    figure;
    
    % Create a subplot for the first star field image
    starfield_im = flip(imread(starfield_path),1);
    subplot(1, 2, 1);
    hold on
    imshow(starfield_im, [], 'XData', phi_ax, 'YData', theta_ax);
    set(gca, 'YDir', 'normal'); % Set the y-axis direction to normal (increasing from bottom to top)
    plot([phi-FOV/2, phi+FOV/2, phi+FOV/2, phi-FOV/2, phi-FOV/2], [-FOV/2, -FOV/2, FOV/2, FOV/2, -FOV/2], 'red');
    plot([phi, phi], [-FOV/2, FOV/2], 'red');
    plot([phi-FOV/2, phi+FOV/2], [0,0], 'red');
    scatter(star_table(:,1), star_table(:,2), 100, 'red', 'MarkerEdgeColor', 'red', 'MarkerFaceColor', 'none');
    scatter(star_table(star_num,1), star_table(star_num,2), 300, 'green', 'MarkerEdgeColor', 'green', 'MarkerFaceColor', 'none', 'Marker', 'x');
    hold off
    title('Star Field 1'); % Title for the first subplot
    axis on
    % Set axes background color to black
    ax = gca; % Get current axes
    ax.Color = [0 0 0]; % Black background
    xlabel('Azimuth (\phi)');
    ylabel('Inclination (\theta)');

    % Create a subplot for the synthetic star tracker image
    subplot(1, 2, 2);
    hold on
    imshow(st_im, [], 'XData', linspace(-FOV/2,FOV/2,nres), 'YData', linspace(-FOV/2,FOV/2,nres));
    set(gca, 'YDir', 'normal');
    scatter(star_ls(:, 1), star_ls(:, 2), 200, 'yellow', 'MarkerEdgeColor', 'yellow', 'MarkerFaceColor', 'none');
    scatter(deltaphi, deltatheta, 200, 'green', 'MarkerEdgeColor', 'green', 'MarkerFaceColor', 'none');
    scatter(star_table(:,1)-phi, star_table(:,2), 250, 'red', 'MarkerEdgeColor', 'red', 'MarkerFaceColor', 'none');
    scatter(deltaphi, deltatheta, 200, 'green', 'MarkerEdgeColor', 'green', 'MarkerFaceColor', 'none', 'Marker', 'x');
    hold off
    title('Star Tracker Image'); % Title for the second subplot
    axis on
    xlim([-FOV/2, FOV/2]); % Set x-axis limits from -FOV/2 to FOV/2
    xlabel('Azimuth (\delta\phi)');
    ylabel('Inclination (\delta\theta)');

end    

function star_table = generate_star_table(n_stars,FOV,nres,spacing_fact)
    % Input: 
    % n_stars: integer, number of stars to include in table
    % FOV: float, angular field of view of camera, in radians, from 0 to 2pi
    % nres: integer, number of pixels on side of image
    % spacing_fact: integer, minimum spacing of stars (as a factor of
    % FOV/nres)

    % Output:
    % star_table: n_stars x 3 array, where column 1 is phi position of
    % star, column 2 is theta position, column 3 is relative brightness
    % (capped at 1)
    
    % Declare empty array
    star_table = zeros(n_stars, 3);

    % Iterate through array, generating random location and brightness
    for istar = 1:n_stars

        % Make sure stars are a set distance apart
        min_dist = spacing_fact*FOV/nres;
        too_close = true;
        if istar > 1
            while too_close
                iphi = -pi/4 + (pi)*rand;
                itheta = -pi/24 + (pi/12)*rand;
                distances = sqrt((iphi-star_table(1:istar,1)).^2+(itheta-star_table(1:istar,2)).^2);
                if min(distances) > min_dist
                    too_close = false;
                end
            end
        else
            iphi = -pi/4 + (pi)*rand;
            itheta = -pi/12 + (pi/6)*rand;
        end
        % Declare parameters for star brightness variation
        mu = 0.5;        % mean
        sigma = 0.1;     % standard deviation
        x_min = 0;    % lower bound
        x_max = 1;     % upper bound
        
        accepted = false;
        while ~accepted
            ibrightness = normrnd(mu, sigma);
            if ibrightness >= x_min && ibrightness <= x_max
                accepted = true;
            end
        end

        % Save values to present row of array
        star_table(istar,:) = [iphi itheta ibrightness];

    end
end

function star_table = import_star_table(star_table_path,x0,y0,nwpx,nhpx,wFOV,hFOV)
    % Input: 
    % filename: str, a .csv file which is nx2, representing the
    % pixel coords of the stars in a full star field image
    % x0: int, x pixel coord of reference star 
    % y0: int, x pixel coord of reference star 
    % nwpx: int, number of pixels of width of starfield image
    % nhpx: int, number of pixels of height of starfield image
    % wFOV: float, field of view width of starfield image [deg]
    % hFOV: float, field of view height of starfield image [deg]
    % Output:
    % star_table: n_stars x 3 array, where column 1 is phi position of
    % star, column 2 is theta position

    % Read in csv
    pixel_table = readmatrix(star_table_path);

    % Index the first column of the pixel_table to get the phi positions
    phi_positions = (pixel_table(:, 1)-x0) * pi/180 * wFOV/nwpx;
    
    % Index the second column of the pixel_table to get the theta positions
    theta_positions = (pixel_table(:, 2)-y0) * pi/180 * hFOV/nhpx;

    % Combine the phi, theta, and brightness into the star_table
    star_table = [phi_positions, theta_positions];

end

function star_lookup = generate_star_lookup_table(star_table, nangle)
    % Input
    % star_table: nx3 array, from generate_star_table
    % nangle: integer, how many stars to compute angles to from reference
    % star

    % Output
    % star_lookup: nxnagle array, each row corresponds to given row in
    % star_table, columns are angular distances to nangle closest stars

    % Initialize lookup table
    star_lookup = zeros(size(star_table, 1), nangle);

    % Iterate through each star in the table
    for istar = 1:length(star_table)
        
        % Compute the angular distances from the current star to all other stars
        phi_diff = star_table(istar, 1) - star_table(:, 1);
        theta_diff = star_table(istar, 2) - star_table(:, 2);
        angle_diff = sqrt(phi_diff.^2 + theta_diff.^2);

        % Sort the angular distances and get the indices of the smallest values
        [sorted_angles, ~] = sort(angle_diff);
        star_lookup(istar, :) = sorted_angles(2:min(nangle+1, length(sorted_angles))); % Store the smallest values
    end
end

function st_im = generate_st_im(star_table, phi, FOV, nres, sharpness, bit_depth)
    % Input: 
    % star_table: nx3 array, from generate_star_table
    % phi: float, boresight angle of camera, in radians, from -pi to pi
    % FOV: float, angular field of view of camera, in radians, from 0 to 2pi
    % nres: integer, number of pixels on side of image
    % sharpness: float, degree of function describing sun shape (higher
    % is sharper), recommended 1-5
    % bit_depth: integer, max brightness value of each pixel
    % Output: 
    % st_im: nres x nres array, representing synethic star tracker image
    
    % Initialize the output image
    st_im = zeros(nres, nres);

    % Initialize coordinate arrays
    [phi_im,theta_im] = meshgrid(linspace(phi-FOV/2,phi+FOV/2,nres),linspace(-FOV/2,FOV/2,nres));

    % Loop through each star in the star table
    for i = 1:size(star_table, 1)
        iphi = star_table(i, 1); % Azimuth angle
        itheta = star_table(i, 2); % Inclination angle
        ibrightness = star_table(i, 3); % Relative brightness

        if iphi > phi-FOV/2 && iphi < phi+FOV/2 && itheta>-FOV/2 && itheta<FOV/2
            st_im = st_im + ibrightness * bit_depth * exp(-((((phi_im-iphi).^2+(theta_im-itheta).^2)/(4*FOV*ibrightness/nres)^2).^sharpness));
        end
    end

    
    % Add random noise to the image
    noise_level = bit_depth*0.02; % Adjust the noise level as needed
    noise = noise_level * randn(size(st_im)); % Generate Gaussian noise
    st_im = st_im + noise; % Add noise to the image
    st_im(st_im < 0) = 0; % Ensure no negative values

    % Normalize the image to the range [0, 1]
    st_im(st_im>bit_depth) = bit_depth;

    % Invert vertically, not sure why this is needed
    st_im = flipud(st_im);
end 

function [st_im,nres] = crop_starfield(starfield_path,phi,FOV,x0,y0,nwpx,nhpx,wFOV,hFOV)
    % Input
    % image: str, path to .png field to import of starfield
    % phi: float, boresight angle of camera, in radians, from -pi to pi
    % FOV: float, angular field of view of camera, in radians, from 0 to 2pi
    % x0: int, x pixel coord of reference star 
    % y0: int, x pixel coord of reference star 
    % nwpx: int, number of pixels of width of starfield image
    % nhpx: int, number of pixels of height of starfield image
    % wFOV: float, field of view width of starfield image [deg]
    % hFOV: float, field of view height of starfield image [deg]
    % Output:
    % st_im: nres x nres array, representing synethic star tracker image
    % nres: integer, number of pixels on side of image

    % Load the .png image as a black and white image array
    file = load(starfield_path);
    img = file.img; 
    starfield_im = rgb2gray(img); % Convert the image to grayscale
    starfield_im = flip(starfield_im,1); % Image array is upside down)


    % Create coordinate axes
    x_ax = linspace(1,nwpx,nwpx) - x0;
    y_ax = linspace(1,nhpx,nhpx) - y0;
    phi_ax = x_ax * pi/180 * wFOV/nwpx;
    theta_ax = y_ax * pi/180 * hFOV/nhpx;
    
    % Crop the starfield image based on the field of view and the phi axis
    phi_indices = find(phi_ax >= (phi - FOV/2) & phi_ax <= (phi + FOV/2));
    nres = size(phi_indices,2);
    theta_indices = find(theta_ax >= (-FOV/2) & theta_ax <= (FOV/2)); %y0-round(nres/2):y0-round(nres/2)+nres-1;
    
    % Ensure indices are within bounds
    %phi_indices = max(min(phi_indices, nwpx), 1);
    %theta_indices = max(min(theta_indices, nhpx), 1);
    
    % Crop the image
    st_im = starfield_im(theta_indices, phi_indices);
end

function star_ls = identify_stars(st_im, FOV)
    % Input:
    % st_im: nxn array, representing image from star tracker
    % FOV: float, field of view along each edge of image
    % Output:
    % star_ls: nx2 array, the phi and theta positions (relative to the
    % center of the image) for each star identified

    % Get image dimensions (not passed to function call)
    [theta_nres,phi_nres] = size(st_im);

    % Convert coordinates to phi and theta positions
    phi_positions = linspace(-FOV/2, FOV/2, phi_nres);
    theta_positions = linspace(-FOV/2, FOV/2, theta_nres);
    
    % Identify bright points in the star tracker image
    threshold = 0.4 * 255; % %max(st_im(:)); % Set a threshold to identify bright points
    %[y_coords, x_coords] = find(st_im > threshold); % Find coordinates of bright points
    
    % Create filtered im
    filtered_im = zeros(size(st_im)); % Initialize filtered image
    filtered_im(st_im > threshold) = 1; % Set values to 1 where st_im exceeds threshold

    % Find connected components
    CC = bwconncomp(filtered_im);

    % Create label matrix
    L = labelmatrix(CC);

    imshow(L)

    % Create output array for star positions
    star_ls = zeros(max(L(:)), 2);
    
    % Iterate through each connected component
    for istar = 1:max(L(:))
        % Get the coordinates of the current star cluster
        [y_cluster, x_cluster] = find(L == istar);
        
        % Store the average position of the cluster
        star_ls(istar, 1) = mean(phi_positions(x_cluster)); % Average phi coordinate
        star_ls(istar, 2) = mean(theta_positions(y_cluster)); % Average theta coordinate
    end
    
    % Basic method
    % Find clusters of bright points in the star tracker image
    %star_ls = []; % Initialize output array for star positions
    %visited = false(size(st_im)); % Create a visited array to track processed pixels
    %for i = 1:length(x_coords)
    %    if ~visited(y_coords(i), x_coords(i)) % Check if the pixel has not been visited
    %        % Mark the current pixel as visited
    %        visited(y_coords(i), x_coords(i)) = true;
    %        % Get the coordinates of the current cluster
    %        cluster = [y_coords(i), x_coords(i)];
    %        % Check adjacent pixels
    %        for dy = -1:1
    %            for dx = -1:1
    %                if dy == 0 && dx == 0
    %                    continue; % Skip the current pixel
    %                end
    %                adj_y = y_coords(i) + dy;
    %                adj_x = x_coords(i) + dx;
    %                if adj_y > 0 && adj_y <= size(st_im, 1) && adj_x > 0 && adj_x <= size(st_im, 2)
    %                    if st_im(adj_y, adj_x) > threshold && ~visited(adj_y, adj_x)
    %                        visited(adj_y, adj_x) = true; % Mark as visited
    %                        cluster = [cluster; adj_y, adj_x]; % Add to cluster
    %                    end
    %                end
    %            end
    %        end
    %        % Store the average position of the cluster
    %        star_ls = [star_ls; mean(cluster, 1)]; % Append the mean position of the cluster
    %    end
    %end
    
    % Create output array for star positions
    %star_ls = zeros(length(x_coords), 2);
    %for i = 1:length(x_coords)
    %    star_ls(i, 1) = phi_positions(x_coords(i)); % Phi position
    %    star_ls(i, 2) = theta_positions(y_coords(i)); % Theta position
    %end
end

function [star_num,deltaphi,deltatheta] = match_to_lookup(star_ls,star_pos_error,star_lookup)
    % Input
    % star_ls: nx2 array, the phi and theta positions (relative to the
    % center of the image) for each star identified
    % star_pos_error: float, angular uncertainty in position of stars
    % star_lookup: nxnagle array, each row corresponds to given row in
    % star_table, columns are angular distances to closest stars

    % Output
    % star_num: integer, index number of matched star
    % deltaphi: float, offset in phi of matched star from image center, in
    % radians
    % deltatheta: float, offset in phi of matched star from image center,
    % in radians

    % Iterate through stars in image, starting closest to middle, until we
    % get a positive match
    star_match = false;
    
    % Calculate the sum of squares for each star position
    star_ls_dist = sum(star_ls.^2, 2);
    
    % Sort the star_ls based on the sum of squares
    [~, sorted_indices] = sort(star_ls_dist);
    star_ls = star_ls(sorted_indices, :);

    istar = 1;
    while star_match == false && istar <= length(star_ls)
        % Compute distances to other stars
        phi_diff = star_ls(istar, 1) - star_ls(:, 1);
        theta_diff = star_ls(istar, 2) - star_ls(:, 2);
        angle_diff = sqrt(phi_diff.^2 + theta_diff.^2);

        % Sort the computed angular distances from smallest to largest
        [sorted_angles, ~] = sort(angle_diff);
        
        % Drop the first element of sorted_angles (distance to itself = 0)
        sorted_angles(1) = [];

        % Reduce sorted angles to only be as long as star_lookup is wide
        sorted_angles = sorted_angles(1:min(length(sorted_angles), size(star_lookup, 2)));

        % Create an array of stars within the positional error range
        match_indices = star_lookup(:, 1) >= (sorted_angles(1) - star_pos_error) & ...
                        star_lookup(:, 1) <= (sorted_angles(1) + star_pos_error);
        matched_stars = star_lookup(match_indices, :);

        % Check if that immediately identified the current state. 
        % If not, compare the angular distances one by one, bringing in more to
        % reduce the number of remaining options
        iangle = 2;

        while size(matched_stars,1) > 1 & iangle <= size(star_lookup,2)
            fprintf('Found multiple matches, refining to next angle\n')
            
            % We loop through the remaining matches
            for j = 1:size(match_indices, 1)
                if j ~= 0
                    % Check to see if the next closest star is within error of
                    % any of the neighbouring stars listed in the lookup table
                    % If none of the angles are close enough, then reject this
                    % match
                    if all(abs(star_lookup(j, iangle:end) - sorted_angles(iangle)) > star_pos_error)
                        match_indices(j) = 0; % Set the jth non-zero element of match_indices to zero
                    end
                end 
            end
            matched_stars = star_lookup(match_indices, :);
        
            iangle = iangle + 1;
        end
        
        % Check if we could use this star 
        if size(matched_stars,1) ~= 1
            fprintf('Could not find lookup table match for this star, moving to the next one\n');
            istar = istar + 1; % Move to the next star
        else
            star_num = find(match_indices ~= 0); % Get the row number of the matched star
            deltaphi = star_ls(istar,1); % Offset in phi
            deltatheta = star_ls(istar,2); % Offset in theta
            star_match = true;
            fprintf('Matched with star number %d, and it is offset %.4f radians in phi and %.4f radians in theta from boresight\n', star_num, deltaphi, deltatheta);
        end
    
    % Return error if star tracker failed 
    if star_match == false
        fprintf('Star tracker failed, unable to get a lock on any star.\n')
        star_num = -1;
        deltaphi = nan;
        deltatheta = nan;
    end
    
    end
    
end

function boresight_phi = compute_boresight_phi(star_num,star_table,deltaphi)
    % Input
    % star_num: integer, index number of matched star
    % star_table: n_stars x 3 array, where column 1 is phi position of
    % star, column 2 is theta position, column 3 is relative brightness
    % deltaphi: float, offset in phi of matched star from image center, in
    % radians
    
    % Output
    % boresight_phi: float, actual orientation of the center of the cameras
    % FOV [rad]

    boresight_phi = star_table(star_num,1) - deltaphi;
end
