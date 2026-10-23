-- The native SDK reports an int32 slot count, including empty slots.
-- Validate that value separately from each caller's per-tick work budget.
return function(array)
 local count=array:get_object_count()
 assert(type(count)=='number' and count>0 and count<=0x7fffffff and count%1==0,
  'Invalid native UObject array count: '..tostring(count))
 return count
end
