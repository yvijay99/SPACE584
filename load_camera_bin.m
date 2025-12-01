function [phi_st, t_st, valid_st, phi_ss, t_ss, valid_ss] = load_camera_bin()
%#codegen
% Reads phi_st.bin and phi_ss.bin from ADCS_python folder
% Returns angles, timestamps, and validity flags

    phi_st = 0;
    t_st = 0;
    valid_st_int = int32(0);
    phi_ss = 0;
    t_ss = 0;
    valid_ss_int = int32(0);
    
    % File paths (null-terminated strings for C)
    path_st = ['/ADCS_python/phi_st.bin', char(0)];
    path_ss = ['/ADCS_python/phi_ss.bin', char(0)];
    
    coder.cinclude('load_camera_bin.h');
    coder.ceval('load_camera_bin', ...
        coder.rref(path_st(1)), coder.rref(path_ss(1)), ...
        coder.wref(phi_st), coder.wref(t_st), coder.wref(valid_st_int), ...
        coder.wref(phi_ss), coder.wref(t_ss), coder.wref(valid_ss_int));
    
    valid_st = (valid_st_int == 1);
    valid_ss = (valid_ss_int == 1);

end