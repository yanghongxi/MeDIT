import numpy as np

def Normalize(data):
    data = np.asarray(data)
    if len(np.shape(data)) == 4:
        dim = 2
    if len(np.shape(data)) == 5:
        dim = 3
        
    means = list()
    stds = list()
    for index in range(np.shape(data)[0]):
        temp_data = data[index, ...]
        if dim == 2:
            means.append(np.mean(temp_data, axis=(0, 1)))
            stds.append(np.std(temp_data, axis=(0, 1)))
        if dim == 3:
            means.append(np.mean(temp_data, axis=(0, 1, 2)))
            stds.append(np.std(temp_data, axis=(0, 1, 2)))
            
    means = np.asarray(means)
    stds = np.asarray(stds)
    
    if dim == 2:
        means = means[..., np.newaxis, np.newaxis]
        means = np.transpose(means, (0, 2, 3, 1))
        stds = stds[..., np.newaxis, np.newaxis]
        stds = np.transpose(stds, (0, 2, 3, 1))
    if dim == 3:
        means = means[..., np.newaxis, np.newaxis, np.newaxis]
        means = np.transpose(means, (0, 2, 3, 4, 1))
        stds = stds[..., np.newaxis, np.newaxis, np.newaxis]
        stds = np.transpose(stds, (0, 2, 3, 4, 1))
        stds[stds == 0] = 1
                
    data -= means
    data /= stds
    
    return data

'''This function to normalize the data for each sample and each modaity seperately'''
def NormalizeForModality(data):
    data = np.asarray(data)
    modalites = data.shape[-1]
    samples = data.shape[0]

    for sample in range(samples):
        for modality in range(modalites):
            data[sample, ..., modality] -= np.mean(data[sample, ..., modality])
            data[sample, ..., modality] = np.divide(data[sample, ..., modality], np.std(data[sample, ..., modality]))

    return data


def Normalize01(data):
	new_data = np.asarray(data, dtype=np.float32)
	if len(np.shape(new_data)) == 2 or len(np.shape(new_data)) == 1:
		new_data = new_data - np.min(new_data)
		new_data = new_data / np.max(new_data)
	
	if len(np.shape(new_data)) == 3:
		for slice_index in range(np.shape(new_data)[2]):
			new_data[:, :, slice_index] = new_data[:, :, slice_index] - np.min(new_data[:, :, slice_index])
			if np.max(new_data[:, :, slice_index]) > 0.001:
				new_data[:, :, slice_index] = np.divide(new_data[:, :, slice_index], np.max(new_data[:, :, slice_index]))
	return new_data
	

def IntensityTransfer(image, target_max, target_min, raw_min=-9999, raw_max=-9999):
	assert(target_max >= target_min)

	image = np.float32(image)
	if raw_min == - 9999:
		raw_min = np.min(image)
	if raw_max == - 9999:
		raw_max = np.max(image)
		
	raw_intensity_range = raw_max - raw_min
	target_intensity_range = target_max - target_min
	image = image * target_intensity_range / raw_intensity_range
	image = image - np.min(image) + target_min
	return image
