function t_unix = get_unix_time()
%#codegen
% Returns current Unix time with microsecond precision
% Calls C function get_unix_time_wrapper()

    t_unix = 0;
    
    coder.cinclude('get_unix_time_wrapper.c');
    coder.ceval('get_unix_time_wrapper', coder.wref(t_unix));

end